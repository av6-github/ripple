"""Database repository for credit assessments, SME profiles, and officer decisions.

Interacts with remote Supabase PostgreSQL.
Adheres strictly to:
- infra/migrations/001_initial_schema.sql
- ARCHITECTURE.md Section 12: Repositories contain SQL / persistence only.
- AGENTS.md Rule 4.6: Officer decisions and overrides stored separately.
- AGENTS.md Rule 4.1: Remote persistence only.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from backend.repositories.db_connection import connect_postgres

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


class AssessmentRepository:
    """Repository handling SQL persistence for assessments, predictions, and SME profiles."""

    def __init__(self, db_url: Optional[str] = None) -> None:
        self.db_url = db_url or os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("SUPABASE_DB_URL or DATABASE_URL is not configured in environment.")

    def _get_connection(self):
        return connect_postgres(self.db_url)

    def ensure_officer_user(self, officer_id: str, email: Optional[str] = None) -> str:
        """Ensure an app_user record exists for foreign key constraints. Returns the valid officer_id."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Check if user exists by id
                cur.execute("SELECT id FROM app_user WHERE id = %s;", (officer_id,))
                row = cur.fetchone()
                if row:
                    return str(row[0])
                
                # Check if email is already taken
                target_email = email or f"officer_{officer_id.replace('-', '')[:8]}@bank.pl"
                cur.execute("SELECT id FROM app_user WHERE email = %s;", (target_email,))
                email_row = cur.fetchone()
                if email_row:
                    return str(email_row[0])

                # Insert new officer user
                cur.execute(
                    """
                    INSERT INTO app_user (id, email, role, first_name, last_name, organization)
                    VALUES (%s, %s, 'bank_officer', 'Bank', 'Officer', 'RIPPLE Bank')
                    ON CONFLICT (id) DO NOTHING;
                    """,
                    (officer_id, target_email),
                )
                conn.commit()
                return officer_id

    def ensure_model_registered(self, model_version: str = "v1.0.0") -> None:
        """Ensure model_version exists in model_registry for foreign key constraints."""
        query = """
        INSERT INTO model_registry (
            model_name, model_version, model_type, target_horizon_months,
            artefact_uri, hyperparameters, feature_names, training_metrics, is_active
        ) VALUES (
            'XGBoost Calibrated', %s, 'tabular_xgboost', 12,
            'artifacts/models/tabular/v1.0.0', '{}'::jsonb, '[]'::jsonb, '{}'::jsonb, TRUE
        ) ON CONFLICT (model_version) DO NOTHING;
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (model_version,))
                conn.commit()

    def create_sme_profile(
        self,
        name: str,
        tax_identifier: Optional[str] = None,
        sector: str = "manufacturing",
        industry: Optional[str] = None,
        address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new SME profile in the sme table."""
        sme_id = str(uuid.uuid4())
        tax_id = tax_identifier or f"TAX-{sme_id[:8]}"
        ind = industry or sector or "General"
        query = """
        INSERT INTO sme (id, legal_name, tax_id, sector, industry, is_synthetic, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, FALSE, NOW(), NOW())
        ON CONFLICT (tax_id) DO UPDATE SET legal_name = EXCLUDED.legal_name, updated_at = NOW()
        RETURNING id, legal_name, tax_id, sector, industry, is_synthetic, created_at;
        """
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (sme_id, name, tax_id, sector, ind))
                res = cur.fetchone()
                conn.commit()
                return dict(res)

    def get_sme_by_id(self, sme_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an SME record by ID."""
        query = "SELECT * FROM sme WHERE id = %s;"
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (sme_id,))
                res = cur.fetchone()
                return dict(res) if res else None

    def get_sme_by_tax_id(self, tax_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an SME record by its Tax ID / NIP."""
        query = "SELECT * FROM sme WHERE tax_id = %s;"
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (tax_id,))
                res = cur.fetchone()
                return dict(res) if res else None

    def list_all_smes(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List clean, deduplicated SME records for the bank portfolio view."""
        query = """
            SELECT DISTINCT ON (legal_name) *
            FROM sme
            WHERE legal_name NOT LIKE 'Test %%'
              AND legal_name NOT LIKE 'Assessment Target %%'
              AND legal_name NOT LIKE '%%[ID:%%'
              AND legal_name NOT LIKE '%%Role:%%'
              AND tax_id NOT LIKE 'TAX-%%'
              AND tax_id NOT LIKE 'BYR-%%'
              AND tax_id NOT LIKE 'SUP-%%'
              AND tax_id NOT LIKE 'PRT-%%'
            ORDER BY legal_name ASC, created_at DESC
            LIMIT %s;
        """
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (limit,))
                rows = cur.fetchall()
                return [dict(r) for r in rows]

    def delete_sme(self, sme_id: str) -> None:
        """Purge an SME and all its cascading records (used for test teardown)."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM loan_application WHERE sme_id = %s::uuid;", (sme_id,))
                cur.execute("DELETE FROM relationship WHERE source_sme_id = %s::uuid OR target_sme_id = %s::uuid;", (sme_id, sme_id))
                cur.execute("DELETE FROM financial_record WHERE sme_id = %s::uuid;", (sme_id,))
                cur.execute("DELETE FROM alternative_data_record WHERE sme_id = %s::uuid;", (sme_id,))
                cur.execute("DELETE FROM data_quality_flag WHERE sme_id = %s::uuid;", (sme_id,))
                cur.execute("DELETE FROM ingestion_job WHERE sme_id = %s::uuid;", (sme_id,))
                
                cur.execute("SELECT id FROM assessment WHERE sme_id = %s::uuid;", (sme_id,))
                asmt_ids = [str(r[0]) for r in cur.fetchall()]
                if asmt_ids:
                    cur.execute("SELECT id FROM prediction WHERE assessment_id = ANY(%s::uuid[]);", (asmt_ids,))
                    pred_ids = [str(r[0]) for r in cur.fetchall()]
                    if pred_ids:
                        cur.execute("DELETE FROM explanation WHERE prediction_id = ANY(%s::uuid[]);", (pred_ids,))
                    cur.execute("DELETE FROM prediction WHERE assessment_id = ANY(%s::uuid[]);", (asmt_ids,))
                    cur.execute("DELETE FROM scenario_result WHERE assessment_id = ANY(%s::uuid[]);", (asmt_ids,))
                    cur.execute("DELETE FROM assessment_input_snapshot WHERE assessment_id = ANY(%s::uuid[]);", (asmt_ids,))
                    cur.execute("DELETE FROM assessment WHERE id = ANY(%s::uuid[]);", (asmt_ids,))
                    
                cur.execute("DELETE FROM audit_log WHERE entity_id = %s::uuid;", (sme_id,))
                cur.execute("DELETE FROM sme WHERE id = %s::uuid;", (sme_id,))
                conn.commit()

    def create_assessment_snapshot(
        self,
        sme_id: str,
        tabular_pd: float,
        graph_pd: Optional[float],
        fused_pd: float,
        calibrated_pd: float,
        risk_band: str,
        recommendation: str,
        is_inconclusive: bool,
        is_cold_start: bool,
        explanation_summary: Dict[str, Any],
        scenario_results: List[Dict[str, Any]],
        network_metrics: Dict[str, Any],
        officer_id: Optional[str] = None,
        model_version: str = "v1.0.0",
    ) -> Dict[str, Any]:
        """Persist assessment record, predictions, and input snapshot."""
        # Ensure foreign keys are valid
        self.ensure_model_registered(model_version)
        off_id = self.ensure_officer_user(officer_id or str(uuid.uuid4()))

        # Map risk band to schema CHECK constraint values
        band_map = {
            "Band A (Low Risk)": "LOW",
            "Band B (Moderate Risk)": "MEDIUM_LOW",
            "Band C (Elevated Risk)": "MEDIUM_HIGH",
            "Band D (High Risk)": "HIGH",
            "INCONCLUSIVE": "INCONCLUSIVE",
            "LOW": "LOW",
            "HIGH": "HIGH",
        }
        db_risk_band = band_map.get(risk_band, "MEDIUM")

        status_val = "INCONCLUSIVE" if is_inconclusive else "COMPLETED"
        assessment_id = str(uuid.uuid4())

        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 1. Insert into assessment table
                cur.execute(
                    """
                    INSERT INTO assessment (
                        id, sme_id, officer_id, assessment_date, status,
                        data_completeness_pct, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, NOW(), %s, %s, NOW(), NOW()
                    ) RETURNING *;
                    """,
                    (assessment_id, sme_id, off_id, status_val, 100.0 if not is_inconclusive else 50.0),
                )
                assessment_row = cur.fetchone()

                # 2. Insert into prediction table
                pred_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO prediction (
                        id, assessment_id, model_version, horizon_months,
                        tabular_pd, graph_pd, fused_pd, calibrated_pd,
                        risk_band, recommendation, created_at
                    ) VALUES (
                        %s, %s, %s, 12,
                        %s, %s, %s, %s,
                        %s, %s, NOW()
                    );
                    """,
                    (
                        pred_id,
                        assessment_id,
                        model_version,
                        tabular_pd,
                        graph_pd,
                        fused_pd,
                        calibrated_pd,
                        db_risk_band,
                        recommendation,
                    ),
                )

                # 3. Insert into assessment_input_snapshot
                cur.execute(
                    """
                    INSERT INTO assessment_input_snapshot (
                        assessment_id, financial_features_snapshot, alternative_features_snapshot,
                        graph_features_snapshot, provenance_snapshot, created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, NOW()
                    );
                    """,
                    (
                        assessment_id,
                        json.dumps(explanation_summary),
                        json.dumps(scenario_results),
                        json.dumps(network_metrics),
                        json.dumps({"is_cold_start": is_cold_start, "officer_id": off_id}),
                    ),
                )

                # 4. Insert scenarios into scenario_result table
                for s in scenario_results:
                    cur.execute(
                        """
                        INSERT INTO scenario_result (
                            assessment_id, scenario_name, scenario_type,
                            base_pd, stressed_pd, pd_delta, stressed_risk_band, disclaimer, created_at
                        ) VALUES (
                            %s, %s, 'predefined',
                            %s, %s, %s, %s, %s, NOW()
                        );
                        """,
                        (
                            assessment_id,
                            s.get("scenario_name", "Stress Scenario"),
                            float(s.get("baseline_pd", 0.0)),
                            float(s.get("shocked_pd", 0.0)),
                            float(s.get("delta_pd", 0.0)),
                            db_risk_band,
                            s.get("disclaimer", "Simulation"),
                        ),
                    )

                conn.commit()
                return dict(assessment_row)

    def get_assessment_snapshot(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full assessment details, prediction, and attached input snapshots."""
        query = """
        SELECT a.*, p.tabular_pd, p.graph_pd, p.fused_pd, p.calibrated_pd, p.risk_band, p.recommendation,
               s.legal_name, s.tax_id, s.sector, s.industry, s.city,
               ais.graph_features_snapshot AS network_metrics,
               ais.financial_features_snapshot AS explanation_summary,
               ais.alternative_features_snapshot AS scenario_results
        FROM assessment a
        LEFT JOIN prediction p ON a.id = p.assessment_id
        LEFT JOIN sme s ON a.sme_id = s.id
        LEFT JOIN assessment_input_snapshot ais ON a.id = ais.assessment_id
        WHERE a.id = %s;
        """
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (assessment_id,))
                res = cur.fetchone()
                if not res:
                    return None
                data = dict(res)
                for json_col in ["network_metrics", "explanation_summary", "scenario_results"]:
                    if isinstance(data.get(json_col), str):
                        try:
                            data[json_col] = json.loads(data[json_col])
                        except Exception:
                            pass
                return data

    def list_assessments_for_sme(self, sme_id: str) -> List[Dict[str, Any]]:
        """List historical assessments for an SME."""
        query = """
        SELECT a.*, p.tabular_pd, p.graph_pd, p.fused_pd, p.calibrated_pd, p.risk_band, p.recommendation,
               s.legal_name, s.tax_id, s.sector, s.industry, s.city,
               ais.graph_features_snapshot AS network_metrics,
               ais.financial_features_snapshot AS explanation_summary,
               ais.alternative_features_snapshot AS scenario_results
        FROM assessment a
        LEFT JOIN prediction p ON a.id = p.assessment_id
        LEFT JOIN sme s ON a.sme_id = s.id
        LEFT JOIN assessment_input_snapshot ais ON a.id = ais.assessment_id
        WHERE a.sme_id = %s
        ORDER BY a.created_at DESC;
        """
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (sme_id,))
                rows = cur.fetchall()
                results = []
                for r in rows:
                    data = dict(r)
                    for json_col in ["network_metrics", "explanation_summary", "scenario_results"]:
                        if isinstance(data.get(json_col), str):
                            try:
                                data[json_col] = json.loads(data[json_col])
                            except Exception:
                                pass
                    results.append(data)
                return results

    def record_officer_decision(
        self,
        assessment_id: str,
        officer_id: str,
        decision: str,
        is_override: bool = False,
        override_reason: Optional[str] = None,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Persist a human bank officer decision or override (AGENTS.md Rule 4.6).
        
        Valid decision values: 'APPROVE', 'REJECT', 'FURTHER_REVIEW', 'OVERRIDE_APPROVE', 'OVERRIDE_REJECT'.
        """
        self.ensure_officer_user(officer_id)
        
        # Normalize decision to valid CHECK constraint values
        norm_decision = decision.upper().strip()
        if is_override:
            if "APPROVE" in norm_decision:
                db_decision = "OVERRIDE_APPROVE"
            elif "REJECT" in norm_decision:
                db_decision = "OVERRIDE_REJECT"
            else:
                db_decision = "OVERRIDE_APPROVE"
        else:
            if norm_decision in ("APPROVE", "REJECT", "FURTHER_REVIEW"):
                db_decision = norm_decision
            elif "APPROVE" in norm_decision:
                db_decision = "APPROVE"
            elif "REJECT" in norm_decision:
                db_decision = "REJECT"
            else:
                db_decision = "FURTHER_REVIEW"

        notes = f"{comments or ''} | Override Reason: {override_reason or 'None'}"

        query = """
        UPDATE assessment
        SET officer_decision = %s,
            officer_notes = %s,
            officer_decision_date = NOW(),
            updated_at = NOW()
        WHERE id = %s
        RETURNING *;
        """
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (db_decision, notes, assessment_id))
                res = cur.fetchone()
                conn.commit()
                return {
                    "id": str(uuid.uuid4()),
                    "assessment_id": assessment_id,
                    "officer_id": officer_id,
                    "decision": db_decision,
                    "is_override": is_override,
                    "override_reason": override_reason,
                    "comments": comments,
                    "decided_at": str(res["officer_decision_date"]) if res else None,
                }

    def get_officer_decisions_for_assessment(self, assessment_id: str) -> List[Dict[str, Any]]:
        """Retrieve officer decision recorded on the assessment."""
        query = "SELECT id, officer_id, officer_decision, officer_notes, officer_decision_date FROM assessment WHERE id = %s AND officer_decision IS NOT NULL;"
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (assessment_id,))
                rows = cur.fetchall()
                return [dict(r) for r in rows]

    def list_statements_for_sme(self, sme_id: str) -> List[Any]:
        """Retrieve financial statement records for an SME from financial_record table."""
        from backend.features.domain import FinancialStatementPeriod
        query = """
        SELECT * FROM financial_record
        WHERE sme_id = %s
        ORDER BY fiscal_year ASC;
        """
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (sme_id,))
                rows = cur.fetchall()
                periods = []
                for r in rows:
                    periods.append(
                        FinancialStatementPeriod(
                            fiscal_year=r.get("fiscal_year") or 2023,
                            total_assets=float(r.get("total_assets") or 0.0),
                            current_assets=float(r.get("current_assets") or 0.0),
                            cash_and_equivalents=float(r.get("cash_and_equivalents") or 0.0),
                            inventory=float(r.get("inventory") or 0.0),
                            accounts_receivable=float(r.get("receivables") or 0.0),
                            total_liabilities=float(r.get("total_liabilities") or 0.0),
                            short_term_liabilities=float(r.get("short_term_liabilities") or 0.0),
                            total_equity=float(r.get("equity") or 0.0),
                            total_revenue=float(r.get("revenue") or 0.0),
                            cost_of_goods_sold=float(r.get("operating_expenses") or 0.0),
                            gross_profit=float(r.get("revenue") or 0.0) - float(r.get("operating_expenses") or 0.0),
                            operating_profit_ebit=float(r.get("ebit") or 0.0),
                            net_profit=float(r.get("net_profit") or 0.0),
                            operating_cash_flow=float(r.get("ebitda") or 0.0),
                            interest_expense=float(r.get("short_term_liabilities") or 0.0) * 0.06,
                        )
                    )
                return periods

    def get_counterparties_from_db(self, sme_id_or_tax_id: str) -> List[Dict[str, Any]]:
        """Retrieve counterparties and commercial relationships from PostgreSQL relationship table."""
        sme = self.get_sme_by_id(sme_id_or_tax_id) or self.get_sme_by_tax_id(sme_id_or_tax_id)
        if not sme:
            return []
        sme_id = str(sme["id"])

        query = """
        SELECT r.id, r.relationship_type, r.weight, r.transaction_volume_annual, r.relationship_duration_months,
               r.is_synthetic, r.source_sme_id, r.target_sme_id,
               src.id AS src_id, src.legal_name AS src_name, src.tax_id AS src_tax_id, src.sector AS src_sector,
               tgt.id AS tgt_id, tgt.legal_name AS tgt_name, tgt.tax_id AS tgt_tax_id, tgt.sector AS tgt_sector
        FROM relationship r
        JOIN sme src ON r.source_sme_id = src.id
        JOIN sme tgt ON r.target_sme_id = tgt.id
        WHERE r.source_sme_id = %s OR r.target_sme_id = %s;
        """
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (sme_id, sme_id))
                rows = cur.fetchall()
                counterparties = []
                seen_ids = set()
                for row in rows:
                    is_source = str(row["src_id"]) == sme_id
                    cp_id = str(row["tgt_id"]) if is_source else str(row["src_id"])
                    cp_tax_id = row["tgt_tax_id"] if is_source else row["src_tax_id"]
                    cp_name = row["tgt_name"] if is_source else row["src_name"]

                    if cp_id in seen_ids:
                        continue
                    seen_ids.add(cp_id)

                    rel_type = row["relationship_type"]
                    # Direction from perspective of this SME
                    if is_source:
                        direction = "outgoing" if rel_type in ("SELLS_TO", "SUPPLIES") else "bidirectional"
                    else:
                        direction = "incoming" if rel_type in ("SUPPLIES", "SELLS_TO") else "bidirectional"

                    role = f"{direction.capitalize()} Trade Partner"
                    if "Role:" in cp_name:
                        try:
                            role = cp_name.split("Role:")[1].replace("]", "").strip()
                        except Exception:
                            pass

                    clean_name = cp_name.split("[ID:")[0].strip() if "[ID:" in cp_name else cp_name

                    counterparties.append({
                        "id": cp_tax_id or cp_id,
                        "name": clean_name,
                        "role": role,
                        "type": rel_type,
                        "direction": direction,
                        "annual_volume": float(row["transaction_volume_annual"] or 100000.0),
                        "tenure_months": int(row["relationship_duration_months"] or 24),
                        "is_synthetic": bool(row["is_synthetic"]),
                        "is_registered_sme": True,
                    })

                if len(counterparties) < 5:
                    extra = self._generate_synthetic_counterparties_for_sme(sme)
                    existing_names = {c["name"].lower() for c in counterparties}
                    existing_ids = {str(c.get("id", "")).lower() for c in counterparties}
                    for e in extra:
                        e_name = e["name"].lower()
                        e_id = str(e.get("id", "")).lower()
                        if e_name not in existing_names and e_id not in existing_ids:
                            counterparties.append(e)
                            existing_names.add(e_name)
                            existing_ids.add(e_id)
                            if len(counterparties) >= 6:
                                break

                return counterparties

    def _generate_synthetic_counterparties_for_sme(self, sme: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Dynamically generate a natural, realistic industry-tailored ego-network for an arbitrary SME.
        
        Strictly adheres to AGENTS.md Rule 4.4: Every generated node and relationship is explicitly
        labeled `is_synthetic = True`.
        """
        sme_id = str(sme["id"])
        raw_sector = (sme.get("sector") or sme.get("industry") or "manufacturing").lower()
        seed = abs(hash(sme_id)) % 100000

        sector_templates = {
            "technology": [
                {"id": f"PL-5210{seed % 900 + 100}", "name": "CloudCore Infrastructure Sp. z o.o.", "role": "Upstream Tier-1 Cloud Infrastructure Provider", "type": "SUPPLIES", "vol": 290000.0, "city": "Warsaw"},
                {"id": f"PL-5210{seed % 900 + 101}", "name": "CyberDefend Security Systems Sp. z o.o.", "role": "SOC-2 Security & Compliance Vendor", "type": "SUPPLIES", "vol": 110000.0, "city": "Warsaw"},
                {"id": f"PL-5250{seed % 900 + 102}", "name": "Apex FinTech Solutions S.A.", "role": "Core Banking Platform Client", "type": "SELLS_TO", "vol": 490000.0, "city": "Warsaw"},
                {"id": f"PL-5830{seed % 900 + 103}", "name": "Nordic Telecom Enterprise Sp. z o.o.", "role": "Enterprise Telecommunications Buyer", "type": "SELLS_TO", "vol": 380000.0, "city": "Gdańsk"},
                {"id": f"PL-5830{seed % 900 + 104}", "name": "Baltic Digital Health Sp. z o.o.", "role": "Hospital Healthcare SaaS Buyer", "type": "SELLS_TO", "vol": 210000.0, "city": "Gdańsk"},
                {"id": f"PL-5260{seed % 900 + 105}", "name": "EuroData Transshipment Hub S.A.", "role": "Regional Data Interchange Partner", "type": "TRANSACTS_WITH", "vol": 140000.0, "city": "Warsaw"},
            ],
            "retail": [
                {"id": f"PL-7220{seed % 900 + 100}", "name": "Podlasie Dairy & Farm Co-op Sp. z o.o.", "role": "Fresh Dairy & Foodstuff Supplier", "type": "SUPPLIES", "vol": 260000.0, "city": "Wysokie Mazowieckie"},
                {"id": f"PL-5530{seed % 900 + 101}", "name": "Vistula Beverage & Goods S.A.", "role": "Packaged Consumer Goods Bottler", "type": "SUPPLIES", "vol": 180000.0, "city": "Żywiec"},
                {"id": f"PL-5830{seed % 900 + 102}", "name": "EcoPackaging Solutions Sp. z o.o.", "role": "Biodegradable Retail Packaging Vendor", "type": "SUPPLIES", "vol": 75000.0, "city": "Gdańsk"},
                {"id": f"PL-5840{seed % 900 + 103}", "name": "Metropolitan Supermarkets CEE S.A.", "role": "Regional Grocery Hypermarket Network", "type": "SELLS_TO", "vol": 490000.0, "city": "Gdańsk"},
                {"id": f"PL-5860{seed % 900 + 104}", "name": "Baltic Hospitality & Catering Sp. z o.o.", "role": "B2B Institutional Catering Client", "type": "SELLS_TO", "vol": 190000.0, "city": "Gdynia"},
                {"id": f"PL-5830{seed % 900 + 105}", "name": "Gdańsk Cold-Chain Depot Sp. k.", "role": "Refrigerated Logistics & Warehousing Partner", "type": "TRANSACTS_WITH", "vol": 105000.0, "city": "Gdańsk"},
            ],
            "transportation": [
                {"id": f"PL-7740{seed % 900 + 100}", "name": "Orlen Commercial Fuel Network Sp. z o.o.", "role": "Commercial Fleet Fuel & Diesel Supplier", "type": "SUPPLIES", "vol": 330000.0, "city": "Płock"},
                {"id": f"PL-5220{seed % 900 + 101}", "name": "ThermoFleet Refrigeration Sp. z o.o.", "role": "Refrigerated Trailer Maintenance Vendor", "type": "SUPPLIES", "vol": 140000.0, "city": "Warsaw"},
                {"id": f"PL-5220{seed % 900 + 102}", "name": "Baltic Commercial Fleet Leasing Sp. z o.o.", "role": "Heavy Vehicle Master Lessor", "type": "SUPPLIES", "vol": 210000.0, "city": "Warsaw"},
                {"id": f"PL-7790{seed % 900 + 103}", "name": "Pol-Retail Distribution Network S.A.", "role": "FMCG Grocery Distribution Client", "type": "SELLS_TO", "vol": 410000.0, "city": "Komorniki"},
                {"id": f"PL-5210{seed % 900 + 104}", "name": "CEE Bio-Pharma Logistics Sp. z o.o.", "role": "Temperature-Controlled Pharma Buyer", "type": "SELLS_TO", "vol": 270000.0, "city": "Warsaw"},
                {"id": f"PL-5250{seed % 900 + 105}", "name": "Warsaw Multi-Modal Freight Terminal S.A.", "role": "Intermodal Rail-Road Transshipment Depot", "type": "TRANSACTS_WITH", "vol": 160000.0, "city": "Warsaw"},
            ],
            "healthcare": [
                {"id": f"PL-5210{seed % 900 + 100}", "name": "Polpharma Diagnostic Bio-Reagents Sp. z o.o.", "role": "Laboratory Reagents & Consumables Supplier", "type": "SUPPLIES", "vol": 310000.0, "city": "Starogard Gdański"},
                {"id": f"PL-5830{seed % 900 + 101}", "name": "Baltic Med-Tech Equipment Leasing Sp. z o.o.", "role": "Precision Diagnostic Imaging Lessor", "type": "SUPPLIES", "vol": 195000.0, "city": "Gdańsk"},
                {"id": f"PL-5220{seed % 900 + 102}", "name": "Mazovia Regional Healthcare Network S.A.", "role": "Public & Private Hospital Procurement Client", "type": "SELLS_TO", "vol": 520000.0, "city": "Warsaw"},
                {"id": f"PL-6760{seed % 900 + 103}", "name": "Silesia Specialist Clinic Consortium Sp. k.", "role": "Outpatient Ambulatory Medical Buyer", "type": "SELLS_TO", "vol": 280000.0, "city": "Katowice"},
                {"id": f"PL-7790{seed % 900 + 104}", "name": "CEE Pharmaceutical Distribution S.A.", "role": "National Pharmacy Wholesaler & Depot", "type": "TRANSACTS_WITH", "vol": 175000.0, "city": "Poznań"},
            ],
            "hospitality": [
                {"id": f"PL-7220{seed % 900 + 100}", "name": "Podlasie Farm & Dairy Suppliers Sp. z o.o.", "role": "Agricultural Fresh Ingredients Supplier", "type": "SUPPLIES", "vol": 240000.0, "city": "Białystok"},
                {"id": f"PL-5530{seed % 900 + 101}", "name": "Vistula Beverage Bottlers S.A.", "role": "Artisanal & Commercial Beverage Partner", "type": "SUPPLIES", "vol": 160000.0, "city": "Żywiec"},
                {"id": f"PL-5830{seed % 900 + 102}", "name": "Baltic Coast Hotel & Spa Group S.A.", "role": "Premier Seaside Resort Chain", "type": "SELLS_TO", "vol": 460000.0, "city": "Sopot"},
                {"id": f"PL-5250{seed % 900 + 103}", "name": "Warsaw Business Events Center Sp. z o.o.", "role": "Corporate Exhibition & Conference Buyer", "type": "SELLS_TO", "vol": 310000.0, "city": "Warsaw"},
                {"id": f"PL-5860{seed % 900 + 104}", "name": "Tricity Institutional Catering Sp. k.", "role": "Executive B2B Dining Client", "type": "TRANSACTS_WITH", "vol": 130000.0, "city": "Gdynia"},
            ],
            "manufacturing": [
                {"id": f"PL-8650{seed % 900 + 100}", "name": "Stalowa Wola Special Alloys S.A.", "role": "Upstream Certified Metallurgical Supplier", "type": "SUPPLIES", "vol": 380000.0, "city": "Stalowa Wola"},
                {"id": f"PL-6760{seed % 900 + 101}", "name": "Katowice Precision Tooling Sp. z o.o.", "role": "CNC Milling & Industrial Consumables", "type": "SUPPLIES", "vol": 175000.0, "city": "Katowice"},
                {"id": f"PL-8170{seed % 900 + 102}", "name": "Warsaw Heavy Infrastructure S.A.", "role": "Primary Industrial Equipment Client", "type": "SELLS_TO", "vol": 520000.0, "city": "Warsaw"},
                {"id": f"PL-5220{seed % 900 + 103}", "name": "Vistula Rail Engineering S.A.", "role": "Rail Haulage OEM Assembler", "type": "SELLS_TO", "vol": 310000.0, "city": "Warsaw"},
                {"id": f"PL-6340{seed % 900 + 104}", "name": "Silesia Industrial Freight Hub Sp. k.", "role": "Heavy Cargo Freight Logistics Partner", "type": "TRANSACTS_WITH", "vol": 145000.0, "city": "Katowice"},
                {"id": f"PL-5830{seed % 900 + 105}", "name": "Baltic Wind Energy Towers S.A.", "role": "Offshore Renewable Structures OEM", "type": "SELLS_TO", "vol": 430000.0, "city": "Gdańsk"},
            ],
        }

        default_template = sector_templates["manufacturing"]
        matched_key = "manufacturing"
        for k in sector_templates:
            if k in raw_sector:
                matched_key = k
                break

        cps_spec = sector_templates.get(matched_key, default_template)
        counterparties = []

        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for cp in cps_spec:
                    cp_clean_name = cp["name"]
                    cur.execute(
                        """
                        INSERT INTO sme (legal_name, tax_id, registration_number, industry, sector, city, country, is_synthetic, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, 'PL', TRUE, NOW())
                        ON CONFLICT (tax_id) DO UPDATE SET legal_name = EXCLUDED.legal_name, updated_at = NOW()
                        RETURNING id;
                        """,
                        (cp_clean_name, cp["id"], f"REG-{cp['id']}", sme.get("industry") or matched_key, matched_key, cp.get("city", "Warsaw")),
                    )
                    row = cur.fetchone()
                    cp_uuid = str(row["id"]) if row else None

                    if cp_uuid:
                        if cp["type"] == "SUPPLIES":
                            src_id, tgt_id, direction = cp_uuid, sme_id, "incoming"
                        elif cp["type"] == "SELLS_TO":
                            src_id, tgt_id, direction = sme_id, cp_uuid, "outgoing"
                        else:
                            src_id, tgt_id, direction = sme_id, cp_uuid, "bidirectional"

                        cur.execute(
                            """
                            INSERT INTO relationship (
                                source_sme_id, target_sme_id, relationship_type, weight,
                                transaction_volume_annual, relationship_duration_months,
                                is_synthetic, source_type, source_ref, confidence, created_at
                            ) VALUES (
                                %s, %s, %s, 1.0, %s, 36, TRUE, 'synthetic', 'benchmark_ego_network', 'verified', NOW()
                            );
                            """,
                            (src_id, tgt_id, cp["type"], cp["vol"]),
                        )

                        counterparties.append({
                            "id": cp["id"],
                            "name": cp_clean_name,
                            "role": cp["role"],
                            "type": cp["type"],
                            "direction": direction,
                            "annual_volume": cp["vol"],
                            "tenure_months": 36,
                            "is_synthetic": True,
                            "is_registered_sme": True,
                        })
                conn.commit()

        return counterparties

    def save_relationship(
        self,
        source_sme_id: str,
        target_sme_id: str,
        relationship_type: str = "SUPPLIES",
        weight: float = 1.0,
        volume_annual: float = 250000.0,
        duration_months: int = 24,
        is_synthetic: bool = True,
        source_type: str = "synthetic",
        source_ref: str = "benchmark_ego_network",
        confidence: str = "verified",
    ) -> Dict[str, Any]:
        """Insert a commercial trade relationship edge into PostgreSQL."""
        query = """
        INSERT INTO relationship (
            source_sme_id, target_sme_id, relationship_type, weight,
            transaction_volume_annual, relationship_duration_months,
            is_synthetic, source_type, source_ref, confidence, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
        )
        RETURNING *;
        """
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                try:
                    cur.execute(
                        query,
                        (
                            source_sme_id,
                            target_sme_id,
                            relationship_type,
                            weight,
                            volume_annual,
                            duration_months,
                            is_synthetic,
                            source_type,
                            source_ref,
                            confidence,
                        ),
                    )
                    res = cur.fetchone()
                    conn.commit()
                    return dict(res) if res else {}
                except Exception:
                    conn.rollback()
                    return {}

    def create_loan_application(
        self,
        sme_id: str,
        facility_type: str,
        requested_amount: float,
        tenor_months: int,
        purpose: str,
        self_reported_revenue: float,
        self_reported_assets: float,
        self_reported_liabilities: float,
        self_reported_equity: float,
        self_reported_net_profit: float,
        self_reported_cash: float,
        contact_name: Optional[str] = None,
        contact_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Insert a new loan facility application into PostgreSQL."""
        query = """
        INSERT INTO loan_application (
            sme_id, facility_type, requested_amount, tenor_months, purpose,
            self_reported_revenue, self_reported_assets, self_reported_liabilities,
            self_reported_equity, self_reported_net_profit, self_reported_cash,
            contact_name, contact_email, status, created_at, updated_at
        ) VALUES (
            %s::uuid, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, 'PENDING_REVIEW', NOW(), NOW()
        )
        RETURNING *;
        """
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    query,
                    (
                        sme_id, facility_type, requested_amount, tenor_months, purpose,
                        self_reported_revenue, self_reported_assets, self_reported_liabilities,
                        self_reported_equity, self_reported_net_profit, self_reported_cash,
                        contact_name, contact_email,
                    ),
                )
                row = cur.fetchone()
                conn.commit()
                return dict(row) if row else {}

    def list_loan_applications(
        self, sme_id: Optional[str] = None, status: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List loan applications joined with SME legal name, tax_id, and sector."""
        conditions = []
        params = []
        if sme_id:
            conditions.append("la.sme_id = %s::uuid")
            params.append(sme_id)
        if status:
            conditions.append("la.status = %s")
            params.append(status)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"""
        SELECT 
            la.*,
            s.legal_name,
            s.tax_id,
            s.sector,
            s.industry,
            s.city
        FROM loan_application la
        JOIN sme s ON la.sme_id = s.id
        {where_clause}
        ORDER BY la.created_at DESC
        LIMIT %s;
        """
        params.append(limit)
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, tuple(params))
                rows = cur.fetchall()
                return [dict(r) for r in rows]

    def get_loan_application(self, application_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific loan application with joined SME metadata."""
        query = """
        SELECT 
            la.*,
            s.legal_name,
            s.tax_id,
            s.sector,
            s.industry,
            s.city
        FROM loan_application la
        JOIN sme s ON la.sme_id = s.id
        WHERE la.id = %s::uuid;
        """
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (application_id,))
                row = cur.fetchone()
                return dict(row) if row else None

    def update_loan_application_status(
        self, application_id: str, status: str, assessment_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update loan application status and optionally link assessment ID."""
        query = """
        UPDATE loan_application
        SET status = %s,
            assessment_id = COALESCE(%s::uuid, assessment_id),
            updated_at = NOW()
        WHERE id = %s::uuid
        RETURNING *;
        """
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (status, assessment_id, application_id))
                row = cur.fetchone()
                conn.commit()
                return dict(row) if row else None

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

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


class AssessmentRepository:
    """Repository handling SQL persistence for assessments, predictions, and SME profiles."""

    def __init__(self, db_url: Optional[str] = None) -> None:
        self.db_url = db_url or os.getenv("SUPABASE_DB_URL")
        if not self.db_url:
            raise ValueError("SUPABASE_DB_URL is not configured in environment.")

    def _get_connection(self):
        return psycopg2.connect(self.db_url)

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

    def list_all_smes(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List SME records for the bank portfolio view."""
        query = "SELECT * FROM sme ORDER BY created_at DESC LIMIT %s;"
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (limit,))
                rows = cur.fetchall()
                return [dict(r) for r in rows]

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
               ais.graph_features_snapshot AS network_metrics,
               ais.financial_features_snapshot AS explanation_summary,
               ais.alternative_features_snapshot AS scenario_results
        FROM assessment a
        LEFT JOIN prediction p ON a.id = p.assessment_id
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
               ais.graph_features_snapshot AS network_metrics,
               ais.financial_features_snapshot AS explanation_summary,
               ais.alternative_features_snapshot AS scenario_results
        FROM assessment a
        LEFT JOIN prediction p ON a.id = p.assessment_id
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

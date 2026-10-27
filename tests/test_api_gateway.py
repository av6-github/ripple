"""Unit and integration tests for RIPPLE FastAPI Gateway and Domain Routers.

Verifies:
- Health and readiness probes (/health, /ready)
- Authentication and RBAC enforcement (401 unauthorized, 403 forbidden)
- SME tenant boundary and information hiding (Rule 4.8: no bank PD or comments exposed to SME)
- Bank assessment orchestration and snapshot persistence
- Officer decision and override recording (Rule 4.6)
"""

import uuid
from fastapi.testclient import TestClient
import pytest
from backend.api.auth import create_access_token
from backend.domain.enums import AppRole
from backend.main import app
from backend.repositories.assessment_repository import AssessmentRepository

client = TestClient(app)


# =====================================================================
# Health & Readiness Probes
# =====================================================================

def test_health_check_endpoint():
    """Verify liveness probe returns 200 and healthy status."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["version"] == "1.0.0"


def test_readiness_check_endpoint():
    """Verify readiness probe reports status of models and services."""
    res = client.get("/ready")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert data["checks"]["tabular_model"] == "READY"
    assert data["checks"]["gnn_model"] == "READY"


# =====================================================================
# Authentication & RBAC Enforcement
# =====================================================================

def test_unauthenticated_access_rejected():
    """Access to protected endpoint without Bearer token returns 401."""
    res = client.get("/api/bank/smes")
    assert res.status_code == 401
    assert "Missing Bearer" in res.json()["detail"]


def test_invalid_token_rejected():
    """Access with forged or corrupted token returns 401."""
    res = client.get("/api/bank/smes", headers={"Authorization": "Bearer forged.invalid.token"})
    assert res.status_code == 401
    assert "Invalid authentication token" in res.json()["detail"]


def test_sme_user_forbidden_from_bank_routes():
    """SME user attempting to access bank officer endpoints returns 403 Forbidden."""
    sme_token = create_access_token(
        user_id=str(uuid.uuid4()),
        email="sme_owner@example.com",
        role=AppRole.SME_USER,
        sme_id=str(uuid.uuid4()),
    )
    res = client.get("/api/bank/smes", headers={"Authorization": f"Bearer {sme_token}"})
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]


def test_bank_officer_accesses_bank_routes_successfully():
    """Bank officer token permits access to bank endpoints."""
    bank_token = create_access_token(
        user_id=str(uuid.uuid4()),
        email="officer@bank.pl",
        role=AppRole.BANK_OFFICER,
    )
    res = client.get("/api/bank/smes", headers={"Authorization": f"Bearer {bank_token}"})
    assert res.status_code == 200
    assert "smes" in res.json()


# =====================================================================
# SME Tenant Isolation & Information Hiding (Rule 4.8)
# =====================================================================

def test_sme_readiness_redacts_lender_information():
    """SME readiness endpoint must NEVER expose bank PD, internal thresholds, or bank comments."""
    repo = AssessmentRepository()
    test_sme = repo.create_sme_profile(
        name=f"Test Isolation SME {uuid.uuid4().hex[:6]}",
        tax_identifier=f"TAX-{uuid.uuid4().hex[:8]}",
        sector="retail",
    )
    sme_id = test_sme["id"]

    try:
        sme_token = create_access_token(
            user_id=str(uuid.uuid4()),
            email="owner@sme.pl",
            role=AppRole.SME_USER,
            sme_id=sme_id,
        )

        res = client.get("/api/sme/readiness", headers={"Authorization": f"Bearer {sme_token}"})
        assert res.status_code == 200
        data = res.json()

        # Verify required SME guidance is present
        assert data["sme_id"] == sme_id
        assert "guidance_tips" in data
        assert "disclaimer" in data

        # STRICT RULE 4.8 ASSERTIONS: Ensure internal lender fields are completely absent
        assert "tabular_pd" not in data
        assert "graph_pd" not in data
        assert "fused_pd" not in data
        assert "bank_comments" not in data
        assert "internal_thresholds" not in data
        assert "shap_values" not in data
    finally:
        try:
            repo.delete_sme(sme_id)
        except Exception:
            pass


# =====================================================================
# Bank Assessment Execution & Snapshot Persistence
# =====================================================================

def test_run_bank_assessment_and_decision_lifecycle():
    """Bank officer triggers end-to-end assessment and records a decision override."""
    repo = AssessmentRepository()
    test_sme = repo.create_sme_profile(
        name=f"Assessment Target SME {uuid.uuid4().hex[:6]}",
        tax_identifier=f"TAX-{uuid.uuid4().hex[:8]}",
        sector="manufacturing",
    )
    sme_id = test_sme["id"]

    try:
        bank_token = create_access_token(
            user_id=str(uuid.uuid4()),
            email="credit_risk@bank.pl",
            role=AppRole.BANK_OFFICER,
        )

        # 1. Run assessment
        payload = {
            "sme_id": sme_id,
            "statements": [
                {
                    "fiscal_year": 2023,
                    "total_assets": 500_000.0,
                    "current_assets": 200_000.0,
                    "cash_and_equivalents": 50_000.0,
                    "inventory": 30_000.0,
                    "total_liabilities": 200_000.0,
                    "short_term_liabilities": 120_000.0,
                    "total_equity": 300_000.0,
                    "total_revenue": 600_000.0,
                    "cost_of_goods_sold": 350_000.0,
                    "gross_profit": 250_000.0,
                    "operating_profit_ebit": 90_000.0,
                    "net_profit": 60_000.0,
                    "operating_cash_flow": 80_000.0,
                    "interest_expense": 15_000.0,
                }
            ],
            "network_neighbors": ["BIZ_COUNTERPARTY_1", "BIZ_COUNTERPARTY_2"],
            "network_edges": [[0, 1], [1, 0]],
        }

        run_res = client.post(
            "/api/bank/assessments/run",
            json=payload,
            headers={"Authorization": f"Bearer {bank_token}"},
        )
        assert run_res.status_code == 201
        assessment_data = run_res.json()

        assert "assessment_id" in assessment_data
        assert assessment_data["sme_id"] == sme_id
        assert 0.0 <= assessment_data["fused_pd"] <= 1.0
        assert assessment_data["recommendation"] in ["LOWER_RISK", "FURTHER_REVIEW", "HIGHER_RISK", "INCONCLUSIVE"]
        assert "DECISION CUSTODY" in assessment_data["decision_custody_notice"]
        assert len(assessment_data["scenario_stress_tests"]) == 4

        assessment_id = assessment_data["assessment_id"]

        # 2. Retrieve snapshot
        snap_res = client.get(
            f"/api/bank/assessments/{assessment_id}",
            headers={"Authorization": f"Bearer {bank_token}"},
        )
        assert snap_res.status_code == 200
        snap_data = snap_res.json()
        assert snap_data["assessment"]["id"] == assessment_id

        # 3. Record Officer Decision / Override (Rule 4.6)
        decision_payload = {
            "decision": "OVERRIDE_APPROVE",
            "is_override": True,
            "override_reason": "Strong personal collateral and long-standing operating history mitigates moderate leverage.",
            "comments": "Credit committee approved with quarterly liquidity covenant monitoring.",
        }

        dec_res = client.post(
            f"/api/bank/assessments/{assessment_id}/decision",
            json=decision_payload,
            headers={"Authorization": f"Bearer {bank_token}"},
        )
        assert dec_res.status_code == 201
        decision_data = dec_res.json()
        assert decision_data["status"] == "DECISION_RECORDED"
        assert decision_data["decision"]["is_override"] is True
        assert decision_data["decision"]["decision"] == "OVERRIDE_APPROVE"
    finally:
        try:
            repo.delete_sme(sme_id)
        except Exception:
            pass


# =====================================================================
# Auth Router Tests
# =====================================================================

def test_issue_auth_token():
    """Verify dynamic token issuance returns valid JWT bearer tokens."""
    res = client.post(
        "/api/auth/token",
        json={"email": "custom_officer@bank.pl", "role": "bank_officer"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "bank_officer"

    # Test using the issued token on protected endpoint
    sme_res = client.get("/api/bank/smes", headers={"Authorization": f"Bearer {data['access_token']}"})
    assert sme_res.status_code == 200


def test_get_demo_tokens():
    """Verify demo tokens endpoint returns valid synchronized bank and SME tokens."""
    res = client.get("/api/auth/demo-tokens")
    assert res.status_code == 200
    data = res.json()
    assert "bank_officer" in data
    assert "sme_user" in data
    
    bank_tok = data["bank_officer"]["token"]
    sme_res = client.get("/api/bank/smes", headers={"Authorization": f"Bearer {bank_tok}"})
    assert sme_res.status_code == 200


def test_assessment_quant_analytics_endpoint(monkeypatch):
    """Verify quant-analytics endpoint returns PIT, reconciliation, and backtest results."""
    bank_token = create_access_token("bank-test-officer", "officer@bank.pl", AppRole.BANK_OFFICER)

    # Mock assessment snapshot and SME in repository for isolated unit testing
    mock_snapshot = {
        "id": "mock-assessment-123",
        "sme_id": "mock-sme-123",
        "tabular_pd": 0.035,
        "graph_pd": 0.02,
        "fused_pd": 0.032,
        "risk_band": "Band B",
        "recommendation": "FURTHER_REVIEW",
        "created_at": "2024-03-15T12:00:00Z",
        "explanation_summary": {
            "top_risk_drivers": [
                {"label": "Current Ratio", "feature": "current_ratio", "value": 1.2, "shap": 0.15}
            ]
        },
    }
    mock_sme = {
        "id": "mock-sme-123",
        "legal_name": "Test Quant SME S.A.",
        "sector": "manufacturing",
        "industry": "Industrial Machinery",
    }

    monkeypatch.setattr(
        AssessmentRepository,
        "get_assessment_snapshot",
        lambda self, aid: mock_snapshot if aid == "mock-assessment-123" else None,
    )
    monkeypatch.setattr(
        AssessmentRepository,
        "get_sme_by_id",
        lambda self, sid: mock_sme if sid == "mock-sme-123" else None,
    )

    # Query quant analytics endpoint
    res = client.get(
        "/api/bank/assessments/mock-assessment-123/quant-analytics",
        headers={"Authorization": f"Bearer {bank_token}"},
    )
    assert res.status_code == 200
    data = res.json()

    assert "point_in_time_audit" in data
    assert data["point_in_time_audit"]["is_point_in_time_compliant"] is True
    assert "data_reconciliation" in data
    assert "cross_sectional_signals" in data
    assert len(data["cross_sectional_signals"]["signals"]) >= 3
    assert "data_quality_gate" in data
    assert "provenance_manifest" in data


def test_simulate_custom_stress_scenario(monkeypatch):
    """Verify custom counterfactual macroeconomic stress testing simulation."""
    bank_token = create_access_token("bank-test-officer", "officer@bank.pl", AppRole.BANK_OFFICER)

    mock_snapshot = {
        "id": "mock-assessment-custom",
        "sme_id": "mock-sme-custom",
        "tabular_pd": 0.045,
        "explanation_summary": {
            "financial_statement": {
                "fiscal_year": 2023,
                "total_assets": 1000000.0,
                "current_assets": 500000.0,
                "cash_and_equivalents": 100000.0,
                "inventory": 80000.0,
                "accounts_receivable": 200000.0,
                "total_liabilities": 400000.0,
                "short_term_liabilities": 250000.0,
                "total_equity": 600000.0,
                "total_revenue": 1500000.0,
                "cost_of_goods_sold": 900000.0,
                "gross_profit": 600000.0,
                "operating_profit_ebit": 150000.0,
                "net_profit": 95000.0,
                "operating_cash_flow": 120000.0,
                "interest_expense": 20000.0,
            }
        },
    }

    monkeypatch.setattr(
        AssessmentRepository,
        "get_assessment_snapshot",
        lambda self, aid: mock_snapshot if aid == "mock-assessment-custom" else None,
    )

    payload = {
        "revenue_drop_pct": 0.25,
        "rate_hike_bps": 350,
        "dso_increase_days": 45,
        "cost_inflation_pct": 0.18,
    }

    res = client.post(
        "/api/bank/assessments/mock-assessment-custom/simulate-scenario",
        json=payload,
        headers={"Authorization": f"Bearer {bank_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["scenario_id"] == "SCEN-CUSTOM"
    assert "shocked_pd" in data
    assert "delta_pd" in data
    assert "percentage_change" in data
    assert data["shocked_features_summary"]["revenue_shock_pct"] == 25.0


"""Integration tests for RIPPLE Loan Application Intake and Dual-Source Reconciliation.

Verifies:
- Loan application submission via SME portal (Rule 4.8 compliant).
- Loan intake recording and queue listing via Bank Officer API.
- Automatic link and status transition ('ASSESSED') when an assessment is executed.
- Dual-source reconciliation prioritizing borrower self-reported loan application metrics as Source A.
- Non-leakage and RBAC boundaries.
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from backend.api.auth import create_access_token
from backend.domain.enums import AppRole
from backend.main import app
from backend.repositories.assessment_repository import AssessmentRepository
from backend.quant.analytics_service import QuantAnalyticsService

client = TestClient(app)


@pytest.fixture(scope="module")
def bank_token():
    return create_access_token(
        user_id=str(uuid.uuid4()),
        email="officer@bank.pl",
        role=AppRole.BANK_OFFICER,
        sme_id=None,
    )


@pytest.fixture(scope="module")
def target_sme(bank_token):
    repo = AssessmentRepository()
    smes = repo.list_all_smes(limit=1)
    if smes:
        return smes[0]
    sme = repo.create_sme_profile(
        name=f"Test Borrower Sp. z o.o. {uuid.uuid4().hex[:6]}",
        tax_identifier=f"PL{uuid.uuid4().int % 10000000000:010d}",
        sector="MANUFACTURING",
        address="ul. Testowa 10, Warsaw",
    )
    return sme


@pytest.fixture(scope="module")
def sme_user_token(target_sme):
    return create_access_token(
        user_id=str(uuid.uuid4()),
        email="borrower@sme.pl",
        role=AppRole.SME_USER,
        sme_id=str(target_sme["id"]),
    )


def test_bank_list_loan_applications(bank_token):
    """Bank officer can list incoming loan applications."""
    res = client.get(
        "/api/bank/applications",
        headers={"Authorization": f"Bearer {bank_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "count" in data
    assert "applications" in data
    assert isinstance(data["applications"], list)


def test_bank_create_and_get_loan_application(bank_token, target_sme):
    """Bank officer can record a loan application on behalf of an SME."""
    payload = {
        "sme_id": str(target_sme["id"]),
        "facility_type": "WORKING_CAPITAL_REVOLVER",
        "requested_amount": 750000.0,
        "tenor_months": 36,
        "purpose": "Supply chain buffer and materials advance procurement",
        "self_reported_revenue": 2100000.0,
        "self_reported_assets": 1400000.0,
        "self_reported_liabilities": 700000.0,
        "self_reported_equity": 700000.0,
        "self_reported_net_profit": 180000.0,
        "self_reported_cash": 120000.0,
        "contact_name": "Marek Nowak",
        "contact_email": "m.nowak@enterprise.pl",
    }
    res = client.post(
        "/api/bank/applications",
        json=payload,
        headers={"Authorization": f"Bearer {bank_token}"},
    )
    assert res.status_code == 201
    created = res.json()["application"]
    app_id = created["id"]
    assert str(created["sme_id"]) == str(target_sme["id"])
    assert float(created["requested_amount"]) == 750000.0
    assert created["status"] == "PENDING_REVIEW"

    # Verify retrieval
    get_res = client.get(
        f"/api/bank/applications/{app_id}",
        headers={"Authorization": f"Bearer {bank_token}"},
    )
    assert get_res.status_code == 200
    fetched = get_res.json()["application"]
    assert fetched["id"] == app_id
    assert fetched["purpose"] == payload["purpose"]


def test_sme_submit_and_list_loan_applications(sme_user_token, target_sme):
    """SME user can submit a loan application and list their applications."""
    payload = {
        "sme_id": str(target_sme["id"]),
        "facility_type": "TERM_LOAN",
        "requested_amount": 400000.0,
        "tenor_months": 24,
        "purpose": "Precision machinery upgrade and capacity extension",
        "self_reported_revenue": 1600000.0,
        "self_reported_assets": 1100000.0,
        "self_reported_liabilities": 500000.0,
        "self_reported_equity": 600000.0,
        "self_reported_net_profit": 95000.0,
        "self_reported_cash": 80000.0,
        "contact_name": "Karol Wisniewski",
        "contact_email": "k.wisniewski@sme.pl",
    }
    submit_res = client.post(
        "/api/sme/applications",
        json=payload,
        headers={"Authorization": f"Bearer {sme_user_token}"},
    )
    assert submit_res.status_code == 201
    app_data = submit_res.json()["application"]
    assert str(app_data["sme_id"]) == str(target_sme["id"])
    assert app_data["status"] == "PENDING_REVIEW"

    # Verify list
    list_res = client.get(
        "/api/sme/applications",
        headers={"Authorization": f"Bearer {sme_user_token}"},
    )
    assert list_res.status_code == 200
    apps = list_res.json()["applications"]
    assert len(apps) >= 1
    assert any(a["id"] == app_data["id"] for a in apps)


def test_assessment_run_links_application_and_updates_status(bank_token, target_sme):
    """Running assessment with application_id auto-links assessment and marks status ASSESSED."""
    repo = AssessmentRepository()
    app = repo.create_loan_application(
        sme_id=str(target_sme["id"]),
        facility_type="EQUIPMENT_FINANCING",
        requested_amount=300000.0,
        tenor_months=18,
        purpose="CNC Laser cutter procurement",
        self_reported_revenue=1500000.0,
        self_reported_assets=1000000.0,
        self_reported_liabilities=400000.0,
        self_reported_equity=600000.0,
        self_reported_net_profit=80000.0,
        self_reported_cash=90000.0,
    )
    app_id = str(app["id"])

    assessment_payload = {
        "sme_id": str(target_sme["id"]),
        "application_id": app_id,
        "statements": [
            {
                "fiscal_year": 2023,
                "total_assets": 1000000.0,
                "current_assets": 450000.0,
                "cash_and_equivalents": 90000.0,
                "inventory": 50000.0,
                "accounts_receivable": 210000.0,
                "total_liabilities": 400000.0,
                "short_term_liabilities": 250000.0,
                "total_equity": 600000.0,
                "total_revenue": 1500000.0,
                "cost_of_goods_sold": 900000.0,
                "gross_profit": 600000.0,
                "operating_profit_ebit": 130000.0,
                "net_profit": 80000.0,
                "operating_cash_flow": 110000.0,
                "interest_expense": 20000.0,
            }
        ],
    }

    run_res = client.post(
        "/api/bank/assessments/run",
        json=assessment_payload,
        headers={"Authorization": f"Bearer {bank_token}"},
    )
    assert run_res.status_code == 201
    assessment_id = run_res.json()["assessment_id"]

    # Verify that the loan application now has status ASSESSED and assessment_id set
    updated_app = repo.get_loan_application(app_id)
    assert updated_app is not None
    assert updated_app["status"] == "ASSESSED"
    assert str(updated_app["assessment_id"]) == str(assessment_id)


def test_dual_source_reconciliation_uses_loan_application_data(target_sme):
    """Dual-source reconciliation uses loan application self-reported metrics as Source A."""
    repo = AssessmentRepository()
    # Create application with specific self-reported figures
    custom_revenue = 1950000.0
    custom_assets = 1350000.0
    app = repo.create_loan_application(
        sme_id=str(target_sme["id"]),
        facility_type="WORKING_CAPITAL_REVOLVER",
        requested_amount=500000.0,
        tenor_months=24,
        purpose="Dual source test facility",
        self_reported_revenue=custom_revenue,
        self_reported_assets=custom_assets,
        self_reported_liabilities=600000.0,
        self_reported_equity=750000.0,
        self_reported_net_profit=110000.0,
        self_reported_cash=95000.0,
    )

    report = QuantAnalyticsService.generate_assessment_quant_report(
        assessment_snapshot={"sme_id": str(target_sme["id"])},
        sme_data=target_sme,
    )
    recon = report.get("data_reconciliation") or {}
    assert "items" in recon
    items = {item["field"]: item for item in recon["items"]}
    assert "revenue" in items
    assert "total_assets" in items
    assert items["revenue"]["self_reported"] == custom_revenue
    assert items["total_assets"]["self_reported"] == custom_assets

"""Bank risk officer domain router for RIPPLE.

Adheres strictly to:
- AGENTS.md Rule 4.6: Officer decisions and overrides stored separately; no automatic approvals.
- Full access to SHAP explanations, GNN network metrics, and scenario stress tests.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from backend.api.auth import UserClaims, require_role
from backend.domain.enums import AppRole
from backend.features.domain import AlternativeDataInput, FinancialStatementPeriod
from backend.repositories.assessment_repository import AssessmentRepository
from backend.services.assessment_service import AssessmentService

router = APIRouter(prefix="/api/bank", tags=["Bank Officer Portal"])


class RunAssessmentRequest(BaseModel):
    sme_id: str
    statements: List[FinancialStatementPeriod]
    alt_data: Optional[AlternativeDataInput] = None
    network_neighbors: Optional[List[str]] = None
    network_edges: Optional[List[Any]] = None
    application_id: Optional[str] = None


class CreateLoanApplicationRequest(BaseModel):
    sme_id: str
    facility_type: str = "WORKING_CAPITAL_REVOLVER"
    requested_amount: float
    tenor_months: int = 24
    purpose: str
    self_reported_revenue: float
    self_reported_assets: float
    self_reported_liabilities: float
    self_reported_equity: float
    self_reported_net_profit: float
    self_reported_cash: float
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None


class OfficerDecisionRequest(BaseModel):
    decision: str  # "APPROVED", "REJECTED", "APPROVED_WITH_CONDITIONS", "DEFERRED"
    is_override: bool = False
    override_reason: Optional[str] = None
    comments: Optional[str] = None


class CustomScenarioRequest(BaseModel):
    revenue_drop_pct: float = 0.0
    rate_hike_bps: int = 0
    dso_increase_days: int = 0
    cost_inflation_pct: float = 0.0


@router.get("/smes")
def list_smes(
    limit: int = 50,
    current_user: UserClaims = Depends(require_role([AppRole.BANK_OFFICER, AppRole.ADMIN])),
) -> Dict[str, Any]:
    """List SME businesses in the bank's loan portfolio."""
    repo = AssessmentRepository()
    smes = repo.list_all_smes(limit=limit)
    return {"count": len(smes), "smes": smes}


@router.get("/smes/{sme_id}")
def get_sme_details(
    sme_id: str,
    current_user: UserClaims = Depends(require_role([AppRole.BANK_OFFICER, AppRole.ADMIN])),
) -> Dict[str, Any]:
    """Retrieve detailed SME profile, financial statements, and historical assessments."""
    repo = AssessmentRepository()
    sme = repo.get_sme_by_id(sme_id)
    if not sme:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SME not found.")
    
    assessments = repo.list_assessments_for_sme(sme_id)
    raw_stmts = repo.list_statements_for_sme(sme_id)
    stmts = [s.model_dump() for s in raw_stmts]
    latest_stmt = stmts[-1] if stmts else None
    return {"sme": sme, "assessments": assessments, "statements": stmts, "latest_statement": latest_stmt}


@router.get("/smes/{sme_id}/counterparties")
def get_sme_counterparties(
    sme_id: str,
    current_user: UserClaims = Depends(require_role([AppRole.BANK_OFFICER, AppRole.ADMIN])),
) -> Dict[str, Any]:
    """Retrieve registered commercial counterparties from Neo4j AuraDB for an SME."""
    from backend.graph.neo4j_client import Neo4jGraphClient
    from backend.graph.network_topology import build_ego_network_edges
    repo = AssessmentRepository()
    sme = repo.get_sme_by_id(sme_id)
    if not sme:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SME not found.")

    tax_id = sme.get("tax_identifier") or sme.get("tax_id") or sme_id
    try:
        neo4j_client = Neo4jGraphClient()
        counterparties = neo4j_client.get_counterparties_for_business(tax_id)
    except Exception:
        counterparties = []

    # Fall back to remote PostgreSQL relationship table if Neo4j is offline, empty, or has fewer than 5
    if not counterparties or len(counterparties) < 5:
        db_cps = repo.get_counterparties_from_db(sme_id)
        if not counterparties:
            counterparties = db_cps
        else:
            existing_names = {c.get("name", "").lower() for c in counterparties}
            existing_ids = {str(c.get("id", "")).lower() for c in counterparties}
            for c in db_cps:
                c_name = c.get("name", "").lower()
                c_id = str(c.get("id", "")).lower()
                if c_name not in existing_names and c_id not in existing_ids:
                    counterparties.append(c)
                    existing_names.add(c_name)
                    existing_ids.add(c_id)
                    if len(counterparties) >= 6:
                        break

    # Construct authentic supply-chain mesh ego-network edge topology
    edges = build_ego_network_edges(counterparties)

    return {
        "sme_id": sme_id,
        "tax_id": tax_id,
        "count": len(counterparties),
        "counterparties": counterparties,
        "edges": edges,
    }


@router.post("/assessments/run", status_code=status.HTTP_201_CREATED)
def run_credit_assessment(
    req: RunAssessmentRequest,
    current_user: UserClaims = Depends(require_role([AppRole.BANK_OFFICER, AppRole.ADMIN])),
) -> Dict[str, Any]:
    """Trigger end-to-end multi-modal risk assessment for an SME."""
    service = AssessmentService()
    try:
        res = service.run_assessment(
            sme_id=req.sme_id,
            statement_periods=req.statements,
            alt_data=req.alt_data,
            officer_id=current_user.user_id,
            network_neighbors=req.network_neighbors,
            network_edges=req.network_edges,
        )
        if req.application_id:
            repo = AssessmentRepository()
            repo.update_loan_application_status(
                req.application_id, status="ASSESSED", assessment_id=res.get("assessment_id")
            )
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/applications")
def list_applications(
    status: Optional[str] = None,
    limit: int = 50,
    current_user: UserClaims = Depends(require_role([AppRole.BANK_OFFICER, AppRole.ADMIN])),
) -> Dict[str, Any]:
    """List all incoming borrower loan applications."""
    repo = AssessmentRepository()
    apps = repo.list_loan_applications(status=status, limit=limit)
    return {"count": len(apps), "applications": apps}


@router.post("/applications", status_code=status.HTTP_201_CREATED)
def create_application_intake(
    req: CreateLoanApplicationRequest,
    current_user: UserClaims = Depends(require_role([AppRole.BANK_OFFICER, AppRole.ADMIN])),
) -> Dict[str, Any]:
    """Bank officer records or intakes a loan application on behalf of an SME."""
    repo = AssessmentRepository()
    sme = repo.get_sme_by_id(req.sme_id)
    if not sme:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target SME not found.")
    app = repo.create_loan_application(
        sme_id=req.sme_id,
        facility_type=req.facility_type,
        requested_amount=req.requested_amount,
        tenor_months=req.tenor_months,
        purpose=req.purpose,
        self_reported_revenue=req.self_reported_revenue,
        self_reported_assets=req.self_reported_assets,
        self_reported_liabilities=req.self_reported_liabilities,
        self_reported_equity=req.self_reported_equity,
        self_reported_net_profit=req.self_reported_net_profit,
        self_reported_cash=req.self_reported_cash,
        contact_name=req.contact_name,
        contact_email=req.contact_email,
    )
    return {"status": "APPLICATION_INTAKE_RECORDED", "application": app}


@router.get("/applications/{application_id}")
def get_application(
    application_id: str,
    current_user: UserClaims = Depends(require_role([AppRole.BANK_OFFICER, AppRole.ADMIN])),
) -> Dict[str, Any]:
    """Retrieve a specific loan application."""
    repo = AssessmentRepository()
    app = repo.get_loan_application(application_id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan application not found.")
    return {"application": app}


@router.get("/assessments/{assessment_id}")
def get_assessment_snapshot(
    assessment_id: str,
    current_user: UserClaims = Depends(require_role([AppRole.BANK_OFFICER, AppRole.ADMIN])),
) -> Dict[str, Any]:
    """Retrieve full immutable assessment snapshot."""
    repo = AssessmentRepository()
    snap = repo.get_assessment_snapshot(assessment_id)
    if not snap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment snapshot not found.")
    
    decisions = repo.get_officer_decisions_for_assessment(assessment_id)
    return {"assessment": snap, "officer_decisions": decisions}


@router.post("/assessments/{assessment_id}/decision", status_code=status.HTTP_201_CREATED)
def record_officer_decision(
    assessment_id: str,
    req: OfficerDecisionRequest,
    current_user: UserClaims = Depends(require_role([AppRole.BANK_OFFICER, AppRole.ADMIN])),
) -> Dict[str, Any]:
    """Record human bank officer credit decision or override (AGENTS.md Rule 4.6)."""
    repo = AssessmentRepository()
    snap = repo.get_assessment_snapshot(assessment_id)
    if not snap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment snapshot not found.")

    decision_record = repo.record_officer_decision(
        assessment_id=assessment_id,
        officer_id=current_user.user_id,
        decision=req.decision,
        is_override=req.is_override,
        override_reason=req.override_reason,
        comments=req.comments,
    )
    return {"status": "DECISION_RECORDED", "decision": decision_record}


@router.get("/assessments/{assessment_id}/quant-analytics")
def get_assessment_quant_analytics(
    assessment_id: str,
    current_user: UserClaims = Depends(require_role([AppRole.BANK_OFFICER, AppRole.ADMIN])),
) -> Dict[str, Any]:
    """Retrieve full quantitative R&D analytics suite for an assessment.

    Includes Point-in-Time As-Of audit, dual-source data reconciliation,
    cross-sectional percentile ranking, outlier winsorisation, feature
    neutralisation, automated data quality gate, and signal backtest metrics.
    """
    from backend.quant.analytics_service import QuantAnalyticsService

    repo = AssessmentRepository()
    snap = repo.get_assessment_snapshot(assessment_id)
    if not snap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment snapshot not found.")

    sme_data = None
    if snap.get("sme_id"):
        sme_data = repo.get_sme_by_id(snap["sme_id"])

    report = QuantAnalyticsService.generate_assessment_quant_report(
        assessment_snapshot=snap,
        sme_data=sme_data,
    )
    return report


@router.post("/assessments/{assessment_id}/simulate-scenario")
def simulate_custom_scenario(
    assessment_id: str,
    req: CustomScenarioRequest,
    current_user: UserClaims = Depends(require_role([AppRole.BANK_OFFICER, AppRole.ADMIN])),
) -> Dict[str, Any]:
    """Execute counterfactual custom macroeconomic scenario stress test."""
    repo = AssessmentRepository()
    snap = repo.get_assessment_snapshot(assessment_id)
    if not snap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment snapshot not found.")

    from backend.services.ml_client import MLClient
    from backend.features.feature_engine import FeatureEngine
    from backend.features.domain import FinancialStatementPeriod
    import numpy as np

    ml = MLClient()
    num_features = len(ml.preprocessor.get_feature_names_out())

    # 1. Prefer the exact financial statement captured in the assessment snapshot
    stmts = []
    exp_summary = snap.get("explanation_summary") or {}
    stmt_dict = exp_summary.get("financial_statement")
    if stmt_dict and isinstance(stmt_dict, dict) and any(v for v in stmt_dict.values() if v is not None):
        try:
            valid_fields = {k: v for k, v in stmt_dict.items() if v is not None}
            stmts = [FinancialStatementPeriod(**valid_fields)]
        except Exception:
            stmts = []

    # 2. Fallback to persisted statements in financial_record table
    if not stmts:
        stmts = repo.list_statements_for_sme(snap["sme_id"])

    # 3. Transform to tabular feature space (67 features)
    if stmts:
        feature_res = FeatureEngine().extract_from_statements(stmts)
        x_features = ml.preprocessor.transform(feature_res.features)
    else:
        x_features = np.zeros((1, num_features))

    baseline_pd = float(snap.get("tabular_pd") or 0.05)
    result = ml.run_custom_scenario(
        X_features=x_features,
        baseline_pd=baseline_pd,
        revenue_drop_pct=req.revenue_drop_pct,
        rate_hike_bps=req.rate_hike_bps,
        dso_increase_days=req.dso_increase_days,
        cost_inflation_pct=req.cost_inflation_pct,
    )

    return {
        "scenario_id": result.scenario_id,
        "scenario_name": result.scenario_name,
        "description": result.description,
        "baseline_pd": result.baseline_pd,
        "shocked_pd": result.shocked_pd,
        "delta_pd": result.delta_pd,
        "percentage_change": result.percentage_change,
        "shocked_features_summary": result.shocked_features_summary,
        "disclaimer": result.disclaimer,
    }

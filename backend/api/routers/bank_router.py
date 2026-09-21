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


class OfficerDecisionRequest(BaseModel):
    decision: str  # "APPROVED", "REJECTED", "APPROVED_WITH_CONDITIONS", "DEFERRED"
    is_override: bool = False
    override_reason: Optional[str] = None
    comments: Optional[str] = None


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
    """Retrieve detailed SME profile and historical assessments."""
    repo = AssessmentRepository()
    sme = repo.get_sme_by_id(sme_id)
    if not sme:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SME not found.")
    
    assessments = repo.list_assessments_for_sme(sme_id)
    return {"sme": sme, "assessments": assessments}


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
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


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

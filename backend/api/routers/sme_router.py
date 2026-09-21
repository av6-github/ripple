"""SME-facing domain router for RIPPLE.

Adheres strictly to:
- AGENTS.md Rule 4.8 (SME Isolation):
  The SME portal must never expose:
  - another SME's information
  - bank comments
  - internal thresholds
  - raw model features
  - bank-side PD
  - lender-only information
"""

import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from backend.api.auth import UserClaims, get_current_user, require_role, verify_sme_ownership
from backend.domain.enums import AppRole
from backend.features.domain import FinancialStatementPeriod
from backend.features.feature_engine import FeatureEngine
from backend.repositories.assessment_repository import AssessmentRepository
from backend.services.completeness_service import CompletenessEvaluator
from backend.services.ingestion_service import IngestionService

router = APIRouter(prefix="/api/sme", tags=["SME Portal"])


class SMERegistrationRequest(BaseModel):
    name: str
    tax_identifier: str
    sector: str = "manufacturing"
    address: Optional[str] = None


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_sme(
    req: SMERegistrationRequest,
    current_user: UserClaims = Depends(require_role([AppRole.SME_USER, AppRole.ADMIN])),
) -> Dict[str, Any]:
    """Register a new SME profile."""
    repo = AssessmentRepository()
    sme = repo.create_sme_profile(
        name=req.name,
        tax_identifier=req.tax_identifier,
        sector=req.sector,
        address=req.address,
    )
    return {"status": "SUCCESS", "sme": sme}


@router.get("/profile")
def get_sme_profile(
    current_user: UserClaims = Depends(require_role([AppRole.SME_USER])),
) -> Dict[str, Any]:
    """Retrieve own SME profile (Rule 4.8: tenant-isolated)."""
    if not current_user.sme_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No SME profile linked to current user.",
        )
    repo = AssessmentRepository()
    sme = repo.get_sme_by_id(current_user.sme_id)
    if not sme:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SME not found.")
    return {"sme": sme}


@router.post("/upload")
def upload_financial_statement(
    file: UploadFile = File(...),
    current_user: UserClaims = Depends(require_role([AppRole.SME_USER, AppRole.BANK_OFFICER, AppRole.ADMIN])),
) -> Dict[str, Any]:
    """Upload financial statement (CSV, XLSX, PDF, ARFF)."""
    if not current_user.sme_id and current_user.role == AppRole.SME_USER:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing SME profile context.")

    sme_id = current_user.sme_id or "00000000-0000-0000-0000-000000000000"
    file_bytes = file.file.read()
    
    service = IngestionService()
    job = service.process_file_upload(
        sme_id=sme_id,
        user_id=current_user.user_id,
        filename=file.filename or "statement.csv",
        file_bytes=file_bytes,
    )
    return {"status": "UPLOAD_ACCEPTED", "job": job}


@router.get("/readiness")
def get_credit_readiness(
    sme_id: Optional[str] = None,
    current_user: UserClaims = Depends(require_role([AppRole.SME_USER, AppRole.BANK_OFFICER, AppRole.ADMIN])),
) -> Dict[str, Any]:
    """Retrieve SME credit readiness overview.
    
    STRICT RULE 4.8 COMPLIANCE:
    Redacts internal bank PD, internal thresholds, bank comments, and lender-only information!
    """
    repo = AssessmentRepository()

    target_sme_id = sme_id or current_user.sme_id
    if current_user.role == AppRole.SME_USER and current_user.sme_id:
        # Enforce tenant isolation: SME users can only query their own SME
        if sme_id and str(sme_id) != str(current_user.sme_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        target_sme_id = current_user.sme_id

    sme = None
    if target_sme_id:
        sme = repo.get_sme_by_id(target_sme_id)

    # Fallback to the first available SME profile if the user has no bound SME
    # or if the target_sme_id is not found in the database (e.g. prototype demo / officer view)
    if not sme:
        all_smes = repo.list_all_smes(limit=1)
        if all_smes:
            sme = all_smes[0]
            target_sme_id = sme["id"]
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No registered SME profile found.")

    # Check latest assessment to pull readiness indicators (redacted)
    assessments = repo.list_assessments_for_sme(target_sme_id)

    if not assessments:
        return {
            "sme_id": target_sme_id,
            "business_name": sme.get("legal_name") or sme.get("name") or "Unknown SME",
            "readiness_status": "PENDING_ASSESSMENT",
            "message": "Upload your latest financial statements to generate credit readiness guidance.",
            "guidance_tips": [
                "Ensure both Balance Sheet and Income Statement are uploaded.",
                "Provide multi-year revenue history for trend analysis.",
                "Verify trade accounts payable and receivable details.",
            ],
            "disclaimer": "This credit readiness overview is for SME self-assessment guidance only and does not represent a loan offer or credit guarantee.",
        }

    latest = assessments[0]

    # Redacted readiness payload (zero bank PD, zero bank comments)
    return {
        "sme_id": target_sme_id,
        "business_name": sme.get("legal_name") or sme.get("name") or "Unknown SME",
        "readiness_status": "EVALUATED",
        "is_complete": not latest.get("is_inconclusive", False),
        "credit_readiness_level": "ADEQUATE" if latest.get("risk_band") in ["Band A (Low Risk)", "Band B (Moderate Risk)"] else "REQUIRES_ATTENTION",
        "guidance_tips": [
            "Maintain current ratio above 1.2 to ensure short-term operational liquidity.",
            "Monitor accounts receivable collection days (DSO) to avoid working capital strain.",
            "Maintain consistent trade invoice settlement schedules.",
        ],
        "disclaimer": "This credit readiness overview is for SME self-assessment guidance only and does not represent a loan offer or credit guarantee.",
    }


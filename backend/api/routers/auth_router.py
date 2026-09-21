"""Authentication domain router for RIPPLE.

Provides JWT token issuance for development, prototype evaluation, and role switching.
"""

from datetime import timedelta
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from backend.api.auth import create_access_token
from backend.domain.enums import AppRole

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class TokenRequest(BaseModel):
    email: str = "officer@bank.pl"
    role: AppRole = AppRole.BANK_OFFICER
    sme_id: Optional[str] = None
    expires_hours: int = 24


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str
    sme_id: Optional[str] = None


@router.post("/token", response_model=TokenResponse)
def issue_token(req: TokenRequest) -> TokenResponse:
    """Issue a signed JWT access token for a given role and entity."""
    user_id = "00000000-0000-0000-0000-000000000001" if req.role == AppRole.BANK_OFFICER else "00000000-0000-0000-0000-000000000002"
    token = create_access_token(
        user_id=user_id,
        email=req.email,
        role=req.role,
        sme_id=req.sme_id,
        expires_delta=timedelta(hours=req.expires_hours),
    )
    return TokenResponse(
        access_token=token,
        role=req.role.value if isinstance(req.role, AppRole) else str(req.role),
        email=req.email,
        sme_id=req.sme_id,
    )


@router.get("/demo-tokens")
def get_demo_tokens(default_sme_id: Optional[str] = None) -> Dict[str, Any]:
    """Get signed demo tokens synchronized with the active backend JWT secret."""
    from backend.repositories.assessment_repository import AssessmentRepository
    repo = AssessmentRepository()
    
    resolved_sme_id = default_sme_id
    if not resolved_sme_id:
        all_smes = repo.list_all_smes(limit=1)
        if all_smes:
            resolved_sme_id = all_smes[0]["id"]
        else:
            resolved_sme_id = "00000000-0000-0000-0000-000000000002"

    bank_token = create_access_token(
        user_id="00000000-0000-0000-0000-000000000001",
        email="officer@bank.pl",
        role=AppRole.BANK_OFFICER,
        expires_delta=timedelta(days=365),
    )
    sme_token = create_access_token(
        user_id="00000000-0000-0000-0000-000000000002",
        email="owner@sme.pl",
        role=AppRole.SME_USER,
        sme_id=resolved_sme_id,
        expires_delta=timedelta(days=365),
    )
    return {
        "bank_officer": {
            "token": bank_token,
            "role": "bank_officer",
            "email": "officer@bank.pl",
        },
        "sme_user": {
            "token": sme_token,
            "role": "sme_user",
            "email": "owner@sme.pl",
            "sme_id": resolved_sme_id,
        },
    }

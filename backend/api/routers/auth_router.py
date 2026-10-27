"""Authentication domain router for RIPPLE.

Provides user registration, login, profile inspection, and JWT issuance.
"""

from datetime import timedelta
import re
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from backend.api.auth import (
    UserClaims,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from backend.domain.enums import AppRole
from backend.repositories.user_repository import UserRepository

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


class RegisterRequest(BaseModel):
    email: str
    password: str
    role: AppRole = AppRole.SME_USER
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization: Optional[str] = None
    tax_id: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthUserResponse(BaseModel):
    id: str
    email: str
    role: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization: Optional[str] = None
    sme_id: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserResponse


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest) -> LoginResponse:
    """Register a new user account with secure password hashing and initial session."""
    clean_email = req.email.strip().lower()
    if not clean_email or "@" not in clean_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email address.")

    if len(req.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long.",
        )

    user_repo = UserRepository()
    existing_user = user_repo.get_user_by_email(clean_email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    pwd_hash = hash_password(req.password)
    user_record = user_repo.create_user(
        email=clean_email,
        password_hash=pwd_hash,
        role=req.role.value if isinstance(req.role, AppRole) else str(req.role),
        first_name=req.first_name,
        last_name=req.last_name,
        organization=req.organization,
    )

    sme_id: Optional[str] = None
    if req.role == AppRole.SME_USER:
        company_name = req.organization or f"{req.first_name or 'SME'} Enterprise Sp. z o.o."
        sme_record = user_repo.create_sme_for_user(
            user_id=user_record["id"],
            legal_name=company_name,
            tax_id=req.tax_id,
            industry="Commercial Services",
            city="Warsaw",
        )
        sme_id = str(sme_record["id"])

    token = create_access_token(
        user_id=str(user_record["id"]),
        email=user_record["email"],
        role=req.role,
        sme_id=sme_id,
        expires_delta=timedelta(hours=24),
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=AuthUserResponse(
            id=str(user_record["id"]),
            email=user_record["email"],
            role=user_record["role"],
            first_name=user_record.get("first_name"),
            last_name=user_record.get("last_name"),
            organization=user_record.get("organization"),
            sme_id=sme_id,
        ),
    )


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest) -> LoginResponse:
    """Authenticate user with email and password, returning signed JWT and profile."""
    clean_email = req.email.strip().lower()
    user_repo = UserRepository()
    user_record = user_repo.get_user_by_email(clean_email)

    if not user_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stored_hash = user_record.get("password_hash")
    if not stored_hash or not verify_password(req.password, stored_hash):
        # Fallback check for pre-seeded demo accounts if not yet updated with password hash
        demo_passwords = {
            "officer@bank.pl": "RippleBank2026!",
            "lead_officer@bank.pl": "RippleBank2026!",
            "owner@sme.pl": "RippleSme2026!",
        }
        if clean_email in demo_passwords and req.password == demo_passwords[clean_email]:
            # Auto-upgrade password hash in database
            new_hash = hash_password(req.password)
            user_repo.update_password(user_record["id"], new_hash)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    role_val = user_record["role"]
    try:
        app_role = AppRole(role_val)
    except ValueError:
        app_role = AppRole.SME_USER

    sme_id: Optional[str] = None
    if app_role == AppRole.SME_USER:
        sme_record = user_repo.get_sme_for_user(user_record["id"])
        if sme_record:
            sme_id = str(sme_record["id"])
        else:
            # Fallback to PolTech Solutions default demo SME if not explicitly linked
            from backend.repositories.assessment_repository import AssessmentRepository
            all_smes = AssessmentRepository().list_all_smes(limit=1)
            if all_smes:
                sme_id = str(all_smes[0]["id"])
                user_repo.link_sme_to_user(user_record["id"], sme_id)

    token = create_access_token(
        user_id=str(user_record["id"]),
        email=user_record["email"],
        role=app_role,
        sme_id=sme_id,
        expires_delta=timedelta(hours=24),
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=AuthUserResponse(
            id=str(user_record["id"]),
            email=user_record["email"],
            role=role_val,
            first_name=user_record.get("first_name"),
            last_name=user_record.get("last_name"),
            organization=user_record.get("organization"),
            sme_id=sme_id,
        ),
    )


@router.get("/me", response_model=AuthUserResponse)
def get_current_profile(current_user: UserClaims = Depends(get_current_user)) -> AuthUserResponse:
    """Retrieve currently authenticated profile claims."""
    user_repo = UserRepository()
    db_user = user_repo.get_user_by_id(current_user.user_id)
    if db_user:
        return AuthUserResponse(
            id=str(db_user["id"]),
            email=db_user["email"],
            role=db_user["role"],
            first_name=db_user.get("first_name"),
            last_name=db_user.get("last_name"),
            organization=db_user.get("organization"),
            sme_id=current_user.sme_id,
        )
    return AuthUserResponse(
        id=current_user.user_id,
        email=current_user.email,
        role=current_user.role.value if isinstance(current_user.role, AppRole) else str(current_user.role),
        sme_id=current_user.sme_id,
    )


@router.post("/token", response_model=TokenResponse)
def issue_token(req: TokenRequest) -> TokenResponse:
    """Issue a signed JWT access token for a given role and entity (backward-compatible)."""
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

"""Authentication and Role-Based Access Control (RBAC) for RIPPLE.

Implements:
- JWT token validation and generation
- Role verification (bank_officer, sme_user, admin)
- SME tenant boundary enforcement (AGENTS.md Rule 4.8)
"""

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from pydantic import BaseModel
from backend.domain.enums import AppRole

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

JWT_SECRET = os.getenv("JWT_SECRET", "ripple-academic-prototype-secure-jwt-secret-key-2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security_bearer = HTTPBearer(auto_error=False)


class UserClaims(BaseModel):
    """Authenticated user claims extracted from JWT."""
    user_id: str
    email: str
    role: AppRole
    sme_id: Optional[str] = None


def create_access_token(
    user_id: str,
    email: str,
    role: AppRole,
    sme_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(hours=JWT_EXPIRATION_HOURS))
    
    payload = {
        "sub": user_id,
        "email": email,
        "role": role.value if isinstance(role, AppRole) else str(role),
        "sme_id": sme_id,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> UserClaims:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        role_str = payload.get("role", AppRole.SME_USER.value)
        role = AppRole(role_str) if role_str in [r.value for r in AppRole] else AppRole.SME_USER

        return UserClaims(
            user_id=payload["sub"],
            email=payload["email"],
            role=role,
            sme_id=payload.get("sme_id"),
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.InvalidTokenError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
) -> UserClaims:
    """Dependency extracting and validating the current authenticated user."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)


def require_role(allowed_roles: List[AppRole]):
    """Dependency factory enforcing specific application roles."""
    def role_checker(current_user: UserClaims = Depends(get_current_user)) -> UserClaims:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {[r.value for r in allowed_roles]}",
            )
        return current_user
    return role_checker


def verify_sme_ownership(sme_id: str, user: UserClaims) -> None:
    """Enforce SME tenant boundary (AGENTS.md Rule 4.8).
    
    Bank officers and admins have portfolio access; SME users can only access their own SME.
    """
    if user.role in (AppRole.BANK_OFFICER, AppRole.ADMIN):
        return

    if user.role == AppRole.SME_USER:
        if not user.sme_id or str(user.sme_id) != str(sme_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. SME users cannot access records belonging to another SME.",
            )

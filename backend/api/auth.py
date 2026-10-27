"""Authentication and Role-Based Access Control (RBAC) for RIPPLE.

Implements:
- JWT token validation and generation
- Role verification (bank_officer, sme_user, admin)
- SME tenant boundary enforcement (AGENTS.md Rule 4.8)
"""

from datetime import datetime, timedelta, timezone
import hashlib
import logging
import os
from pathlib import Path
import secrets
from typing import List, Optional
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from pydantic import BaseModel
from backend.domain.enums import AppRole

logger = logging.getLogger("ripple-auth")
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

_raw_jwt_secret = os.getenv("JWT_SECRET")
_env_mode = os.getenv("ENVIRONMENT", os.getenv("NODE_ENV", "development")).lower()

if _env_mode in ("production", "staging") and not _raw_jwt_secret:
    raise RuntimeError("CRITICAL SECURITY VIOLATION: JWT_SECRET environment variable must be explicitly configured in production/staging.")

if not _raw_jwt_secret:
    logger.warning("INSECURE JWT CONFIG: Using default academic prototype fallback JWT secret. Set JWT_SECRET in .env for production.")

JWT_SECRET = _raw_jwt_secret or "ripple-academic-prototype-secure-jwt-secret-key-2026"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security_bearer = HTTPBearer(auto_error=False)


def hash_password(plain_password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with 100,000 iterations and salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    )
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored salt and PBKDF2-HMAC-SHA256 hash using constant-time comparison."""
    if not hashed_password or "$" not in hashed_password:
        return False
    try:
        salt, expected_hex = hashed_password.split("$", 1)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000,
        )
        return secrets.compare_digest(key.hex(), expected_hex)
    except Exception:
        return False


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

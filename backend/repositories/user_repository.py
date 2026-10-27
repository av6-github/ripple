"""PostgreSQL User Repository for RIPPLE.

Provides user lookup, registration, credential updates, and SME association in Supabase PostgreSQL.
"""

import os
import uuid
from typing import Any, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from backend.repositories.db_connection import connect_postgres


class UserRepository:
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("SUPABASE_DB_URL or DATABASE_URL is not configured.")

    def _get_connection(self):
        return connect_postgres(self.db_url)

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by normalized lowercase email."""
        clean_email = email.strip().lower()
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, email, role, first_name, last_name, organization, password_hash, created_at, updated_at
                    FROM app_user
                    WHERE LOWER(email) = %s
                    LIMIT 1;
                    """,
                    (clean_email,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by UUID."""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, email, role, first_name, last_name, organization, created_at, updated_at
                    FROM app_user
                    WHERE id = %s
                    LIMIT 1;
                    """,
                    (str(user_id),),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def create_user(
        self,
        email: str,
        password_hash: str,
        role: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        organization: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new user with password hash."""
        uid = str(user_id or uuid.uuid4())
        clean_email = email.strip().lower()
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO app_user (id, email, password_hash, role, first_name, last_name, organization, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING id, email, role, first_name, last_name, organization, created_at;
                    """,
                    (uid, clean_email, password_hash, role, first_name, last_name, organization),
                )
                conn.commit()
                row = cur.fetchone()
                return dict(row)

    def update_password(self, user_id: str, password_hash: str) -> bool:
        """Update user password hash."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE app_user
                    SET password_hash = %s, updated_at = NOW()
                    WHERE id = %s;
                    """,
                    (password_hash, str(user_id)),
                )
                conn.commit()
                return cur.rowcount > 0

    def get_sme_for_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Find SME record linked to a given user_id."""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, legal_name, tax_id, industry, city, country, user_id
                    FROM sme
                    WHERE user_id = %s
                    LIMIT 1;
                    """,
                    (str(user_id),),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def link_sme_to_user(self, user_id: str, sme_id: str) -> bool:
        """Link an existing SME to a user_id."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE sme
                    SET user_id = %s, updated_at = NOW()
                    WHERE id = %s;
                    """,
                    (str(user_id), str(sme_id)),
                )
                conn.commit()
                return cur.rowcount > 0

    def create_sme_for_user(
        self,
        user_id: str,
        legal_name: str,
        tax_id: Optional[str] = None,
        industry: str = "General SME",
        city: str = "Warsaw",
    ) -> Dict[str, Any]:
        """Create a new SME entity linked to this user."""
        sme_id = str(uuid.uuid4())
        clean_tax_id = tax_id or f"PL-{uuid.uuid4().hex[:10].upper()}"
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO sme (id, legal_name, tax_id, industry, city, country, user_id, is_synthetic, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, 'PL', %s, FALSE, NOW(), NOW())
                    RETURNING id, legal_name, tax_id, industry, city, user_id;
                    """,
                    (sme_id, legal_name, clean_tax_id, industry, city, str(user_id)),
                )
                conn.commit()
                row = cur.fetchone()
                return dict(row)

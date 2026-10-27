"""Resilient PostgreSQL Connection Helper for Supabase.

Handles transparent fallback between Supavisor pooler URLs and direct database hosts
to prevent downtime if pooler tenant routing is dropped or modified.
"""

import logging
import os
import urllib.parse
from typing import Optional
import psycopg2

logger = logging.getLogger("ripple-db")


def connect_postgres(db_url: Optional[str] = None):
    """Establish a PostgreSQL connection with automatic pooler-to-direct fallback."""
    url = db_url or os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("SUPABASE_DB_URL or DATABASE_URL is not configured.")

    try:
        return psycopg2.connect(url, connect_timeout=10)
    except psycopg2.OperationalError as e:
        error_msg = str(e)
        # If pooler fails (e.g. tenant not found on pooler proxy), attempt direct connection
        if "pooler.supabase.com" in url or "tenant" in error_msg.lower():
            logger.warning(
                "Supabase pooler connection failed; attempting direct database host fallback: %s",
                error_msg.split("\n")[0],
            )
            try:
                parsed = urllib.parse.urlparse(url)
                username = parsed.username or ""
                if "." in username:
                    user_prefix, ref = username.split(".", 1)
                else:
                    ref = (
                        os.getenv("SUPABASE_URL", "")
                        .replace("https://", "")
                        .replace(".supabase.co", "")
                        .strip()
                    )
                    user_prefix = "postgres"

                if ref:
                    password = urllib.parse.unquote(parsed.password or "")
                    database = parsed.path.lstrip("/") or "postgres"
                    conn = psycopg2.connect(
                        host=f"db.{ref}.supabase.co",
                        port=5432,
                        user=user_prefix,
                        password=password,
                        dbname=database,
                        connect_timeout=10,
                    )
                    logger.info("Successfully connected to direct Supabase host db.%s.supabase.co:5432", ref)
                    return conn
            except Exception as direct_err:
                logger.error("Direct Supabase connection fallback failed: %s", direct_err)
        raise e

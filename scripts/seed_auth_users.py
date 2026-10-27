"""Seed and synchronize test authentication accounts with hashed passwords in PostgreSQL.
"""

import os
import psycopg2
from dotenv import load_dotenv
from backend.api.auth import hash_password

load_dotenv()

DB_URL = os.getenv("SUPABASE_DB_URL")
if not DB_URL:
    raise RuntimeError("SUPABASE_DB_URL is not set.")

USERS_TO_SEED = [
    {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "officer@bank.pl",
        "password": "RippleBank2026!",
        "role": "bank_officer",
        "first_name": "Wojciech",
        "last_name": "Kowalski",
        "organization": "PKO Commercial Credit Risk",
    },
    {
        "id": "00000000-0000-0000-0000-000000000002",
        "email": "owner@sme.pl",
        "password": "RippleSme2026!",
        "role": "sme_user",
        "first_name": "Piotr",
        "last_name": "Nowak",
        "organization": "PolTech Solutions Sp. z o.o.",
    },
]

conn = psycopg2.connect(DB_URL)
with conn.cursor() as cur:
    for u in USERS_TO_SEED:
        pwd_hash = hash_password(u["password"])
        cur.execute(
            """
            INSERT INTO app_user (id, email, password_hash, role, first_name, last_name, organization, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT (email) DO UPDATE
            SET password_hash = EXCLUDED.password_hash,
                role = EXCLUDED.role,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                organization = EXCLUDED.organization,
                updated_at = NOW();
            """,
            (u["id"], u["email"], pwd_hash, u["role"], u["first_name"], u["last_name"], u["organization"]),
        )
        print(f"Upserted user {u['email']} with role {u['role']}")
    conn.commit()

conn.close()
print("Auth users seeded successfully.")

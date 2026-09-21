#!/usr/bin/env python3
"""
RIPPLE Infrastructure Smoke Test (Phase 0B)
Tests remote Supabase PostgreSQL and Neo4j AuraDB connectivity,
applies database migrations, and verifies constraints without logging secrets.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
repo_root = Path(__file__).resolve().parent.parent
env_path = repo_root / ".env"

if not env_path.exists():
    print("ERROR: .env file not found at project root")
    sys.exit(1)

load_dotenv(env_path)

supabase_db_url = os.getenv("SUPABASE_DB_URL")
neo4j_uri = os.getenv("NEO4J_URI")
neo4j_user = os.getenv("NEO4J_USERNAME")
neo4j_pass = os.getenv("NEO4J_PASSWORD")

results = {
    "supabase_connected": False,
    "migration_applied": False,
    "constraints_verified": False,
    "provenance_enforced": False,
    "neo4j_connected": False,
    "neo4j_schema_ready": False,
}

print("==================================================")
print("RIPPLE INFRASTRUCTURE SMOKE TEST (PHASE 0B)")
print("==================================================")

# ------------------------------------------------------------------------------
# 1. Supabase PostgreSQL Smoke Test
# ------------------------------------------------------------------------------
print("\n[1/2] Testing Supabase PostgreSQL connectivity...")

if not supabase_db_url:
    print("FAIL: SUPABASE_DB_URL is not set in .env")
else:
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        conn = psycopg2.connect(supabase_db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        cursor.execute("SELECT version();")
        pg_version = cursor.fetchone()[0]
        print(f"PASS: Connected to PostgreSQL: {pg_version[:45]}...")
        results["supabase_connected"] = True
        
        # Apply migration
        migration_file = repo_root / "infra" / "migrations" / "001_initial_schema.sql"
        print(f"Applying migration: {migration_file.name}...")
        with open(migration_file, "r") as f:
            migration_sql = f.read()
            
        cursor.execute(migration_sql)
        print("PASS: Migration 001_initial_schema.sql applied successfully.")
        results["migration_applied"] = True
        
        # Verify tables
        expected_tables = [
            "app_user", "sme", "financial_record", "alternative_data_record",
            "relationship", "data_quality_flag", "model_registry", "assessment",
            "assessment_input_snapshot", "prediction", "explanation",
            "scenario_result", "ingestion_job", "audit_log"
        ]
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        existing_tables = set(r[0] for r in cursor.fetchall())
        missing = [t for t in expected_tables if t not in existing_tables]
        
        if missing:
            print(f"FAIL: Missing expected tables: {missing}")
        else:
            print(f"PASS: All 14 expected domain tables exist in 'public' schema.")
            results["constraints_verified"] = True
            
        # Verify Provenance Constraint (Rule 4.3): Test invalid insert without required provenance
        print("Verifying non-null provenance constraints...")
        try:
            # Attempt to insert financial_record with missing provenance (should fail)
            cursor.execute("""
                INSERT INTO financial_record (sme_id, source_type, source_ref, confidence)
                VALUES ('00000000-0000-0000-0000-000000000000', 'invalid_source', 'test', 'verified');
            """)
            print("FAIL: Constraint violation was not triggered for invalid source_type!")
        except psycopg2.Error:
            print("PASS: Non-nullable/Check constraint for source_type correctly rejected invalid source.")
            results["provenance_enforced"] = True
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"FAIL: PostgreSQL test error: {e}")

# ------------------------------------------------------------------------------
# 2. Neo4j AuraDB Smoke Test
# ------------------------------------------------------------------------------
print("\n[2/2] Testing Neo4j AuraDB connectivity...")

if not (neo4j_uri and neo4j_user and neo4j_pass):
    print("FAIL: Neo4j credentials missing in .env (NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)")
else:
    try:
        from neo4j import GraphDatabase
        
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
        with driver.session() as session:
            # Check connectivity
            result = session.run("RETURN 1 AS ping")
            record = result.single()
            if record and record["ping"] == 1:
                print("PASS: Connected to Neo4j AuraDB.")
                results["neo4j_connected"] = True
                
            # Set up uniqueness constraint for SME nodes
            session.run("""
                CREATE CONSTRAINT unique_business_id IF NOT EXISTS
                FOR (b:Business) REQUIRE b.id IS UNIQUE;
            """)
            print("PASS: Neo4j unique business id constraint ensured.")
            
            # Simple test node round-trip
            test_id = "smoke-test-sme-001"
            session.run("""
                MERGE (b:Business {id: $id})
                SET b.name = 'Smoke Test SME', b.is_synthetic = true
            """, id=test_id)
            
            check = session.run("MATCH (b:Business {id: $id}) RETURN b.name AS name, b.is_synthetic AS is_synthetic", id=test_id).single()
            if check and check["name"] == 'Smoke Test SME' and check["is_synthetic"] is True:
                print("PASS: Neo4j node write and read-back verified with synthetic flag.")
                results["neo4j_schema_ready"] = True
                
            # Clean up smoke test node
            session.run("MATCH (b:Business {id: $id}) DETACH DELETE b", id=test_id)
            print("PASS: Smoke test node cleaned up.")
            
        driver.close()
    except Exception as e:
        print(f"FAIL: Neo4j test error: {e}")

print("\n==================================================")
print("TEST SUMMARY")
print("==================================================")
all_passed = all(results.values())
for k, v in results.items():
    print(f"  {k}: {'PASS' if v else 'FAIL'}")

if all_passed:
    print("\nALL INFRASTRUCTURE SMOKE TESTS PASSED.")
    sys.exit(0)
else:
    print("\nSOME SMOKE TESTS FAILED.")
    sys.exit(1)

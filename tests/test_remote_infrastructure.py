import os
import uuid
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Load environment
repo_root = Path(__file__).resolve().parent.parent
load_dotenv(repo_root / ".env")

supabase_url = os.getenv("SUPABASE_DB_URL")
neo4j_uri = os.getenv("NEO4J_URI")
neo4j_user = os.getenv("NEO4J_USERNAME")
neo4j_pass = os.getenv("NEO4J_PASSWORD")


@pytest.fixture(scope="session")
def pg_conn():
    if not supabase_url:
        pytest.skip("SUPABASE_DB_URL not set in .env")
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    
    conn = psycopg2.connect(supabase_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def neo4j_driver():
    if not (neo4j_uri and neo4j_user and neo4j_pass):
        pytest.skip("Neo4j credentials not set in .env")
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
    try:
        driver.verify_connectivity()
    except Exception as exc:
        driver.close()
        pytest.skip(f"Neo4j AuraDB instance is unavailable or paused ({exc})")
    yield driver
    driver.close()


def test_supabase_connection(pg_conn):
    cursor = pg_conn.cursor()
    cursor.execute("SELECT 1;")
    res = cursor.fetchone()
    assert res[0] == 1
    cursor.close()


def test_all_14_domain_tables_exist(pg_conn):
    expected_tables = {
        "app_user", "sme", "financial_record", "alternative_data_record",
        "relationship", "data_quality_flag", "model_registry", "assessment",
        "assessment_input_snapshot", "prediction", "explanation",
        "scenario_result", "ingestion_job", "audit_log"
    }
    cursor = pg_conn.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    tables = {r[0] for r in cursor.fetchall()}
    cursor.close()
    
    missing = expected_tables - tables
    assert len(missing) == 0, f"Missing tables: {missing}"


def test_provenance_constraint_enforcement(pg_conn):
    import psycopg2
    cursor = pg_conn.cursor()
    
    # Missing source_type must fail
    with pytest.raises(psycopg2.Error):
        cursor.execute("""
            INSERT INTO financial_record (sme_id, source_ref, confidence)
            VALUES ('00000000-0000-0000-0000-000000000000', 'ref', 'verified');
        """)
        
    # Invalid confidence value must fail CHECK constraint
    with pytest.raises(psycopg2.Error):
        cursor.execute("""
            INSERT INTO financial_record (sme_id, source_type, source_ref, confidence)
            VALUES ('00000000-0000-0000-0000-000000000000', 'public_dataset', 'ref', 'invalid_conf');
        """)
    cursor.close()


def test_crud_sme_and_financial_record_lifecycle(pg_conn):
    cursor = pg_conn.cursor()
    test_id = str(uuid.uuid4())
    legal_name = f"Test SME {test_id[:8]}"
    
    # 1. Create SME
    cursor.execute("""
        INSERT INTO sme (id, legal_name, industry, is_synthetic)
        VALUES (%s, %s, 'Manufacturing', TRUE)
        RETURNING id;
    """, (test_id, legal_name))
    created_id = cursor.fetchone()[0]
    assert created_id == test_id
    
    # 2. Insert financial record with raw ratios JSONB
    fin_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO financial_record (
            id, sme_id, fiscal_year, forecasting_case, source_type, source_ref, confidence,
            target_bankruptcy, target_horizon_months, raw_ratios
        ) VALUES (
            %s, %s, 2024, '1year', 'public_dataset', '1year.arff', 'verified',
            FALSE, 60, '{"Attr1": 0.2005, "Attr2": 0.3795}'::jsonb
        ) RETURNING id, raw_ratios;
    """, (fin_id, test_id))
    
    row = cursor.fetchone()
    assert row[0] == fin_id
    assert row[1]["Attr1"] == 0.2005
    
    # 3. Clean up (CASCADE should remove financial_record)
    cursor.execute("DELETE FROM sme WHERE id = %s;", (test_id,))
    
    cursor.execute("SELECT COUNT(*) FROM financial_record WHERE id = %s;", (fin_id,))
    count = cursor.fetchone()[0]
    assert count == 0
    cursor.close()


def test_neo4j_connectivity_and_schema(neo4j_driver):
    with neo4j_driver.session() as session:
        # Check connectivity
        ping = session.run("RETURN 1 AS val").single()["val"]
        assert ping == 1
        
        # Verify node creation with synthetic label and clean up
        test_node_id = f"test-node-{uuid.uuid4()}"
        session.run("""
            CREATE (b:Business {id: $id, name: 'Test Entity', is_synthetic: true})
        """, id=test_node_id)
        
        node = session.run("MATCH (b:Business {id: $id}) RETURN b.is_synthetic AS synth", id=test_node_id).single()
        assert node["synth"] is True
        
        session.run("MATCH (b:Business {id: $id}) DETACH DELETE b", id=test_node_id)


def test_rls_cross_tenant_isolation(pg_conn):
    """
    DB-004: Verify that SME user A cannot read SME B's data under Supabase RLS.
    """
    cursor = pg_conn.cursor()
    user_a_id = str(uuid.uuid4())
    user_b_id = str(uuid.uuid4())
    sme_a_id = str(uuid.uuid4())
    sme_b_id = str(uuid.uuid4())

    try:
        # 1. Create two SME users
        cursor.execute("""
            INSERT INTO app_user (id, email, role) VALUES 
            (%s, %s, 'sme_user'),
            (%s, %s, 'sme_user');
        """, (user_a_id, f"test_a_{user_a_id[:6]}@test.com", user_b_id, f"test_b_{user_b_id[:6]}@test.com"))

        # 2. Create two SMEs owned by respective users
        cursor.execute("""
            INSERT INTO sme (id, legal_name, industry, user_id, is_synthetic) VALUES
            (%s, 'SME Alpha Tenant', 'Tech', %s, true),
            (%s, 'SME Beta Tenant', 'Retail', %s, true);
        """, (sme_a_id, user_a_id, sme_b_id, user_b_id))

        # 3. Simulate authenticated User A querying SMEs
        cursor.execute("BEGIN;")
        cursor.execute("SET LOCAL ROLE authenticated;")
        cursor.execute("SELECT set_config('request.jwt.claims', %s, true);", (f'{{"sub": "{user_a_id}"}}',))
        cursor.execute("SELECT set_config('request.jwt.claim.sub', %s, true);", (user_a_id,))

        cursor.execute("SELECT id, legal_name FROM sme;")
        visible_smes = cursor.fetchall()
        cursor.execute("ROLLBACK;")

        # User A must ONLY see SME Alpha, NEVER SME Beta
        assert len(visible_smes) == 1, f"Expected 1 SME, got {len(visible_smes)}"
        assert str(visible_smes[0][0]) == sme_a_id
        assert visible_smes[0][1] == "SME Alpha Tenant"

    finally:
        # Clean up
        cursor.execute("DELETE FROM sme WHERE id IN (%s, %s);", (sme_a_id, sme_b_id))
        cursor.execute("DELETE FROM app_user WHERE id IN (%s, %s);", (user_a_id, user_b_id))
        cursor.close()


def test_pinecone_vector_roundtrip():
    """
    Test vector upsert and filtered query in Pinecone index.
    """
    pinecone_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "ripple-sme-embeddings")
    if not pinecone_key or pinecone_key.startswith("your-"):
        pytest.skip("PINECONE_API_KEY not configured")

    from pinecone import Pinecone
    import time

    pc = Pinecone(api_key=pinecone_key)
    idx = pc.Index(index_name)

    test_vec_id = f"test-vec-{uuid.uuid4()}"
    test_values = [0.05] * 64
    
    idx.upsert(
        vectors=[{"id": test_vec_id, "values": test_values, "metadata": {"industry": "Manufacturing"}}],
        namespace="tabular-v1"
    )
    time.sleep(2)

    query_res = idx.query(vector=test_values, top_k=1, namespace="tabular-v1", include_metadata=True)
    assert len(query_res.matches) >= 1
    assert query_res.matches[0].id == test_vec_id
    assert query_res.matches[0].metadata["industry"] == "Manufacturing"

    # Cleanup
    idx.delete(ids=[test_vec_id], namespace="tabular-v1")


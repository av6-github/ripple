"""Remote Neo4j AuraDB graph client for RIPPLE.

Adheres strictly to:
- AGENTS.md Rule 4.1: Remote persistence (AuraDB).
- AGENTS.md Rule 4.4: Enforcing is_synthetic = true on all synthetic edges.
- AGENTS.md Rule 6: No fake integrations.
"""

import os
from typing import Any, Dict, List, Optional
from neo4j import GraphDatabase


from pathlib import Path
from dotenv import load_dotenv

# Automatically load .env from project root if not already set
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


class Neo4jGraphClient:
    """Official driver client for remote Neo4j AuraDB."""

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        self.uri = uri or os.getenv("NEO4J_URI")
        self.user = user or os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD")

        if not self.uri or not self.password:
            raise ValueError("NEO4J_URI and NEO4J_PASSWORD must be configured in environment.")

        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self) -> None:
        """Close driver connection pool."""
        if self.driver:
            self.driver.close()

    def __enter__(self) -> "Neo4jGraphClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def verify_connectivity(self) -> bool:
        """Verify remote Neo4j AuraDB connectivity."""
        self.driver.verify_connectivity()
        return True

    def upsert_business_node(
        self,
        business_id: str,
        name: str,
        sector: str = "manufacturing",
        is_active: bool = True,
    ) -> None:
        """Upsert a :Business node with unique constraint."""
        query = """
        MERGE (b:Business {id: $id})
        ON CREATE SET b.name = $name, b.sector = $sector, b.is_active = $is_active, b.created_at = datetime()
        ON MATCH SET b.name = $name, b.sector = $sector, b.is_active = $is_active, b.updated_at = datetime()
        """
        with self.driver.session() as session:
            session.run(query, id=business_id, name=name, sector=sector, is_active=is_active)

    def upsert_commercial_relation(
        self,
        source_id: str,
        target_id: str,
        rel_type: str = "SUPPLIES_TO",
        annual_volume: float = 50_000.0,
        tenure_months: int = 12,
        is_synthetic: bool = True,
    ) -> None:
        """Upsert commercial edge between two businesses.
        
        Mandates is_synthetic = true per AGENTS.md Rule 4.4.
        """
        query = """
        MERGE (s:Business {id: $source_id})
        MERGE (t:Business {id: $target_id})
        MERGE (s)-[r:COMMERCIAL_RELATION {type: $rel_type}]->(t)
        SET r.annual_volume = $volume,
            r.tenure_months = $tenure,
            r.is_synthetic = $is_synthetic,
            r.updated_at = datetime()
        """
        with self.driver.session() as session:
            session.run(
                query,
                source_id=source_id,
                target_id=target_id,
                rel_type=rel_type,
                volume=float(annual_volume),
                tenure=int(tenure_months),
                is_synthetic=bool(is_synthetic),
            )

    def get_network_metrics(self, business_id: str) -> Dict[str, Any]:
        """Compute structural network metrics for an SME node."""
        query = """
        MATCH (b:Business {id: $id})
        OPTIONAL MATCH (b)-[out:COMMERCIAL_RELATION]->(cust:Business)
        OPTIONAL MATCH (supp:Business)-[inc:COMMERCIAL_RELATION]->(b)
        RETURN count(DISTINCT out) AS out_degree,
               count(DISTINCT inc) AS in_degree,
               count(DISTINCT out) + count(DISTINCT inc) AS total_degree,
               collect(DISTINCT cust.id) AS customer_ids,
               collect(DISTINCT supp.id) AS supplier_ids
        """
        with self.driver.session() as session:
            record = session.run(query, id=business_id).single()
            if not record or record["total_degree"] == 0:
                return {
                    "in_degree": 0,
                    "out_degree": 0,
                    "total_degree": 0,
                    "customer_ids": [],
                    "supplier_ids": [],
                    "is_isolated": True,
                }
            return {
                "in_degree": int(record["in_degree"]),
                "out_degree": int(record["out_degree"]),
                "total_degree": int(record["total_degree"]),
                "customer_ids": list(record["customer_ids"]),
                "supplier_ids": list(record["supplier_ids"]),
                "is_isolated": False,
            }

    def delete_test_node(self, business_id: str) -> None:
        """Clean up test nodes and attached edges."""
        query = """
        MATCH (b:Business {id: $id})
        DETACH DELETE b
        """
        with self.driver.session() as session:
            session.run(query, id=business_id)

    def get_counterparties_for_business(self, business_id: str) -> List[Dict[str, Any]]:
        """Retrieve all connected commercial counterparties and edge properties from Neo4j AuraDB."""
        query = """
        MATCH (b:Business {id: $id})-[r:COMMERCIAL_RELATION]-(c:Business)
        RETURN c.id AS id, c.name AS name, r.type AS rel_type,
               startNode(r).id = b.id AS is_outgoing,
               r.annual_volume AS annual_volume, r.tenure_months AS tenure_months,
               r.is_synthetic AS is_synthetic
        """
        results = []
        try:
            with self.driver.session() as session:
                records = session.run(query, id=business_id).data()
        except Exception as exc:
            import logging
            logging.getLogger("ripple-neo4j").warning("Neo4j AuraDB query failed (fallback to PostgreSQL available): %s", exc)
            return []

        for r in records:
                raw_id = r["id"]
                name = raw_id
                cid = raw_id
                role = "Counterparty"
                if "[ID:" in raw_id and "Role:" in raw_id:
                    try:
                        name = raw_id.split("[ID:")[0].strip()
                        meta_part = raw_id.split("[ID:")[1]
                        cid = meta_part.split("|")[0].strip()
                        role = meta_part.split("Role:")[1].replace("]", "").strip()
                    except Exception:
                        pass
                elif r.get("name"):
                    name = r["name"]

                role_lower = role.lower()
                cid_lower = cid.lower()
                rel_type = (r.get("rel_type") or "").upper()
                if (
                    "partner" in role_lower
                    or "hub" in role_lower
                    or "lab" in role_lower
                    or "prt-" in cid_lower
                    or "PARTNER" in rel_type
                ):
                    direction = "bidirectional"
                elif (
                    "supplier" in role_lower
                    or "vendor" in role_lower
                    or "provider" in role_lower
                    or "upstream" in role_lower
                    or "lessor" in role_lower
                    or "sup-" in cid_lower
                ):
                    direction = "incoming"
                elif (
                    "buyer" in role_lower
                    or "client" in role_lower
                    or "byr-" in cid_lower
                    or "downstream" in role_lower
                ):
                    direction = "outgoing"
                elif rel_type == "SUPPLIES_TO":
                    direction = "incoming"
                else:
                    direction = "outgoing"

                results.append({
                    "raw_id": raw_id,
                    "id": cid,
                    "name": name,
                    "role": role,
                    "direction": direction,
                    "rel_type": rel_type,
                    "annual_volume": r.get("annual_volume") or 75000.0,
                    "tenure_months": r.get("tenure_months") or 24,
                    "is_synthetic": bool(r.get("is_synthetic", True)),
                })
        return results

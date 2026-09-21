"""Synthetic commercial network generator for Polish SME bankruptcy dataset.

Adheres strictly to:
- AGENTS.md Rule 4.4: Every synthetic relationship must be explicitly labelled is_synthetic = true.
- Generates realistic scale-free supplier/customer supply-chain connections.
"""

from dataclasses import dataclass
import random
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np


@dataclass
class SyntheticEdge:
    """A commercial relationship edge between two businesses."""
    source_id: str
    target_id: str
    relationship_type: str  # "SUPPLIES_TO" or "PURCHASES_FROM"
    annual_volume: float
    tenure_months: int
    is_synthetic: bool = True  # Non-negotiable per AGENTS.md Rule 4.4


class SyntheticGraphGenerator:
    """Generates synthetic commercial supply-chain networks connecting SME nodes."""

    def __init__(self, random_seed: int = 42) -> None:
        self.random_seed = random_seed
        self.rng = random.Random(random_seed)
        self.np_rng = np.random.default_rng(random_seed)

    def generate_network(
        self,
        business_ids: List[str],
        avg_degree: float = 3.0,
        density: float = 0.005,
    ) -> List[SyntheticEdge]:
        """Generate a realistic commercial network connecting the provided business IDs.
        
        Uses preferential attachment / scale-free dynamics to mirror real-world supply chains
        where a few large hub suppliers serve many downstream SMEs.
        """
        n = len(business_ids)
        if n < 2:
            return []

        edges: List[SyntheticEdge] = []
        existing_edges: Set[Tuple[str, str]] = set()

        # Degree sequence via power-law / preferential attachment
        degrees: Dict[str, int] = {bid: 1 for bid in business_ids}
        hub_count = max(2, int(n * 0.05))
        hubs = business_ids[:hub_count]

        # Target total edges
        target_edges = int(n * (avg_degree / 2.0))

        # 1. Connect hubs to a core skeleton
        for i in range(len(hubs) - 1):
            u, v = hubs[i], hubs[i + 1]
            if (u, v) not in existing_edges:
                vol = float(round(self.rng.uniform(100_000, 1_000_000), 2))
                tenure = self.rng.randint(24, 120)
                edge = SyntheticEdge(
                    source_id=u,
                    target_id=v,
                    relationship_type="SUPPLIES_TO",
                    annual_volume=vol,
                    tenure_months=tenure,
                    is_synthetic=True,
                )
                edges.append(edge)
                existing_edges.add((u, v))
                degrees[u] += 1
                degrees[v] += 1

        # 2. Preferential attachment connections for remaining nodes
        node_pool = list(business_ids)
        attempts = 0
        max_attempts = target_edges * 10

        while len(edges) < target_edges and attempts < max_attempts:
            attempts += 1
            # Sample source node
            u = self.rng.choice(node_pool)
            # Sample target node with probability proportional to current degree
            weights = [degrees[b] for b in business_ids]
            tot_w = sum(weights)
            probs = [w / tot_w for w in weights]
            v = self.np_rng.choice(business_ids, p=probs)

            if u == v or (u, v) in existing_edges or (v, u) in existing_edges:
                continue

            vol = float(round(self.rng.uniform(20_000, 500_000), 2))
            tenure = self.rng.randint(6, 60)
            rel_type = "SUPPLIES_TO" if self.rng.random() > 0.5 else "PURCHASES_FROM"

            edge = SyntheticEdge(
                source_id=u,
                target_id=str(v),
                relationship_type=rel_type,
                annual_volume=vol,
                tenure_months=tenure,
                is_synthetic=True,  # Mandatory Rule 4.4
            )
            edges.append(edge)
            existing_edges.add((u, str(v)))
            degrees[u] += 1
            degrees[str(v)] += 1

        # Strict validation: verify every single generated edge has is_synthetic = True
        for e in edges:
            if not e.is_synthetic:
                raise ValueError("AGENTS.md Rule 4.4 Violation: Synthetic edge missing is_synthetic=True!")

        return edges

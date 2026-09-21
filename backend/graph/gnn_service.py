"""Service managing GNN inference, embeddings, and cold-start fallback.

Adheres strictly to:
- AGENTS.md Rule 4.2: No Fabricated Risk (isolated nodes trigger fallback, no fabricated PD).
- AGENTS.md Rule 4.4: Enforcing is_synthetic = true on synthetic relationships.
- TESTS.md GNN-004: Fallback triggered when isolated / cold start.
"""

from dataclasses import dataclass, field
import json
import os
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import torch
from backend.graph.gnn_model import SMEGraphNeuralNetwork


@dataclass
class NetworkRiskAssessment:
    """Network risk assessment result for an SME."""
    business_id: str
    graph_pd: Optional[float]
    is_cold_start: bool
    fallback_triggered: bool
    fallback_reason: Optional[str]
    in_degree: int
    out_degree: int
    total_degree: int
    embedding: Optional[List[float]] = None
    flags: Dict[str, Any] = field(default_factory=dict)


class GNNService:
    """Orchestrates network credit scoring, structural embeddings, and cold-start fallback."""

    def __init__(
        self,
        model_dir: str = "artifacts/models/gnn/v1.0.0",
        device: str = "cpu",
    ) -> None:
        self.model_dir = model_dir
        self.device = torch.device(device)
        self.model: Optional[SMEGraphNeuralNetwork] = None
        self.config: Dict[str, Any] = {}
        self._load_model_if_available()

    def _load_model_if_available(self) -> None:
        weights_path = os.path.join(self.model_dir, "gnn_weights.pt")
        config_path = os.path.join(self.model_dir, "config.json")

        if os.path.exists(weights_path) and os.path.exists(config_path):
            with open(config_path, "r") as f:
                self.config = json.load(f)
            
            self.model = SMEGraphNeuralNetwork(
                in_channels=self.config.get("in_channels", 67),
                hidden_channels=self.config.get("hidden_channels", 32),
                embedding_dim=self.config.get("embedding_dim", 16),
            ).to(self.device)
            
            state_dict = torch.load(weights_path, map_location=self.device, weights_only=True)
            self.model.load_state_dict(state_dict)
            self.model.eval()

    def assess_network_risk(
        self,
        business_id: str,
        node_features: Optional[np.ndarray] = None,
        neighbor_ids: Optional[List[str]] = None,
        network_edges: Optional[List[Tuple[int, int]]] = None,
        subgraph_features: Optional[np.ndarray] = None,
    ) -> NetworkRiskAssessment:
        """Evaluate network risk for a business.
        
        If isolated (degree = 0) or no graph available, triggers cold-start fallback policy (GNN-004).
        """
        # Check cold-start condition: no neighbors, empty edges, or missing node/subgraph features
        has_network = (
            neighbor_ids is not None
            and len(neighbor_ids) > 0
            and network_edges is not None
            and len(network_edges) > 0
            and subgraph_features is not None
        )

        if not has_network or self.model is None:
            # Fallback policy per AGENTS.md Rule 4.2
            fallback_reason = "gnn_model_unavailable" if self.model is None else (
                "missing_subgraph_features" if (neighbor_ids and network_edges and subgraph_features is None) else "isolated_node_zero_degree"
            )
            return NetworkRiskAssessment(
                business_id=business_id,
                graph_pd=None,
                is_cold_start=True,
                fallback_triggered=True,
                fallback_reason=fallback_reason,
                in_degree=0,
                out_degree=0,
                total_degree=0,
                embedding=None,
                flags={"synthetic_connections": False, "requires_tabular_fallback": True},
            )

        # Connected node inference
        with torch.no_grad():
            x_tensor = torch.tensor(subgraph_features, dtype=torch.float32).to(self.device)
            edge_index = torch.tensor(network_edges, dtype=torch.long).t().contiguous().to(self.device)

            logits, embeddings = self.model(x_tensor, edge_index)
            probas = torch.softmax(logits, dim=-1)
            # Target node is index 0 in the ego-subgraph
            target_pd = float(probas[0, 1].item())
            target_emb = [round(float(v), 5) for v in embeddings[0].cpu().numpy()]

        deg = len(neighbor_ids)
        return NetworkRiskAssessment(
            business_id=business_id,
            graph_pd=round(target_pd, 4),
            is_cold_start=False,
            fallback_triggered=False,
            fallback_reason=None,
            in_degree=deg // 2,
            out_degree=deg - (deg // 2),
            total_degree=deg,
            embedding=target_emb,
            flags={"synthetic_connections": True, "requires_tabular_fallback": False},
        )

"""PyTorch Geometric Dataset Builder for RIPPLE Graph Models.

Adheres strictly to:
- TESTS.md GNN-001: Disjoint train, validation, and test masks.
- TESTS.md GNN-002: Feature alignment with tabular feature order.
- TESTS.md GNN-003: Synthetic relationships explicitly marked.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import torch
from torch_geometric.data import Data
from backend.graph.synthetic_generator import SyntheticEdge


def build_pyg_graph_data(
    X_features: np.ndarray,
    y_labels: np.ndarray,
    edges: List[SyntheticEdge],
    business_ids: List[str],
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    random_seed: int = 42,
) -> Data:
    """Construct PyTorch Geometric Data object with disjoint masks and aligned features."""
    n_nodes = len(business_ids)
    if n_nodes != len(X_features) or n_nodes != len(y_labels):
        raise ValueError("Mismatch in node counts across features, labels, and IDs.")

    # 1. Node Feature Tensor (dim 67, matching preprocessor output order GNN-002)
    x_tensor = torch.tensor(X_features, dtype=torch.float32)
    y_tensor = torch.tensor(y_labels, dtype=torch.long)

    # 2. Edge Index and Attributes
    id_to_idx = {bid: i for i, bid in enumerate(business_ids)}
    src_indices: List[int] = []
    dst_indices: List[int] = []
    edge_features: List[List[float]] = []

    for edge in edges:
        if edge.source_id in id_to_idx and edge.target_id in id_to_idx:
            u = id_to_idx[edge.source_id]
            v = id_to_idx[edge.target_id]
            src_indices.append(u)
            dst_indices.append(v)
            # Edge attributes: [normalized_volume, is_synthetic_flag]
            vol_norm = float(np.log1p(max(0.0, edge.annual_volume)))
            is_synth = 1.0 if edge.is_synthetic else 0.0
            edge_features.append([vol_norm, is_synth])

    if src_indices:
        edge_index = torch.tensor([src_indices, dst_indices], dtype=torch.long)
        edge_attr = torch.tensor(edge_features, dtype=torch.float32)
    else:
        edge_index = torch.empty((2, 0), dtype=torch.long)
        edge_attr = torch.empty((0, 2), dtype=torch.float32)

    # 3. Disjoint Masks (GNN-001)
    rng = np.random.default_rng(random_seed)
    shuffled_indices = rng.permutation(n_nodes)

    train_end = int(n_nodes * train_ratio)
    val_end = int(n_nodes * (train_ratio + val_ratio))

    train_idx = set(shuffled_indices[:train_end])
    val_idx = set(shuffled_indices[train_end:val_end])
    test_idx = set(shuffled_indices[val_end:])

    # Strict assertion of disjointness
    assert len(train_idx.intersection(val_idx)) == 0, "Train and Val masks overlap!"
    assert len(train_idx.intersection(test_idx)) == 0, "Train and Test masks overlap!"
    assert len(val_idx.intersection(test_idx)) == 0, "Val and Test masks overlap!"

    train_mask = torch.zeros(n_nodes, dtype=torch.bool)
    val_mask = torch.zeros(n_nodes, dtype=torch.bool)
    test_mask = torch.zeros(n_nodes, dtype=torch.bool)

    train_mask[list(train_idx)] = True
    val_mask[list(val_idx)] = True
    test_mask[list(test_idx)] = True

    return Data(
        x=x_tensor,
        edge_index=edge_index,
        edge_attr=edge_attr,
        y=y_tensor,
        train_mask=train_mask,
        val_mask=val_mask,
        test_mask=test_mask,
        num_nodes=n_nodes,
    )

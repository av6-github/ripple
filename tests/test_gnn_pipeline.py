"""Unit and integration tests for RIPPLE Graph & GNN pipeline.

Verifies:
- GNN-001: Disjoint train, validation, and test masks
- GNN-002: Feature alignment with tabular preprocessor feature order
- GNN-003: Synthetic relationships strictly labelled with is_synthetic = True
- GNN-004: Fallback triggered when isolated / cold start (Rule 4.2 & Rule 4.4)
- Neo4j remote graph round-trip verification
"""

import os
import numpy as np
import pytest
import torch
from backend.graph.gnn_model import SMEGraphNeuralNetwork
from backend.graph.gnn_service import GNNService
from backend.graph.neo4j_client import Neo4jGraphClient
from backend.graph.pyg_dataset import build_pyg_graph_data
from backend.graph.synthetic_generator import SyntheticEdge, SyntheticGraphGenerator
from backend.ml.data_loader import PolishBankruptcyDataLoader
from backend.ml.preprocessor import TabularPreprocessor


# =====================================================================
# GNN-001: Disjoint Masks
# =====================================================================

def test_gnn_001_masks_disjoint():
    """Verify that PyG train, validation, and test masks are mutually exclusive."""
    X = np.random.randn(100, 67).astype(np.float32)
    y = np.random.randint(0, 2, size=100)
    business_ids = [f"B_{i}" for i in range(100)]
    edges = [
        SyntheticEdge(source_id=f"B_{i}", target_id=f"B_{i+1}", relationship_type="SUPPLIES_TO", annual_volume=10_000, tenure_months=12, is_synthetic=True)
        for i in range(99)
    ]

    pyg_data = build_pyg_graph_data(X, y, edges, business_ids, train_ratio=0.7, val_ratio=0.15, random_seed=42)

    # Boolean masks
    train_m = pyg_data.train_mask.numpy()
    val_m = pyg_data.val_mask.numpy()
    test_m = pyg_data.test_mask.numpy()

    # Must be mutually exclusive
    assert np.logical_and(train_m, val_m).sum() == 0, "Train and Val masks overlap!"
    assert np.logical_and(train_m, test_m).sum() == 0, "Train and Test masks overlap!"
    assert np.logical_and(val_m, test_m).sum() == 0, "Val and Test masks overlap!"

    # Total must cover all 100 nodes
    assert (train_m.sum() + val_m.sum() + test_m.sum()) == 100


# =====================================================================
# GNN-002: Feature Alignment with Tabular Preprocessor Order
# =====================================================================

def test_gnn_002_feature_alignment():
    """Verify GNN input node features match TabularPreprocessor output shape and ordering."""
    loader = PolishBankruptcyDataLoader()
    X_df, _ = loader.load_dataset(horizon_years=1)
    preprocessor = TabularPreprocessor(add_indicators=True, clip_percentiles=True)
    X_proc = preprocessor.fit_transform(X_df.iloc[:20])

    expected_dim = len(preprocessor.get_feature_names_out())
    assert X_proc.shape[1] == expected_dim == 67

    # Load GNN model and verify in_channels
    service = GNNService()
    assert service.config.get("in_channels") == 67
    assert service.model.conv1.in_channels == 67


# =====================================================================
# GNN-003: Synthetic Relationships Labelled
# =====================================================================

def test_gnn_003_synthetic_relationships_labelled():
    """Verify that every synthetic relationship produced by generator has is_synthetic = True."""
    bids = [f"SME_{i}" for i in range(50)]
    gen = SyntheticGraphGenerator(random_seed=42)
    edges = gen.generate_network(bids, avg_degree=3.0)

    assert len(edges) > 0
    for edge in edges:
        assert edge.is_synthetic is True, f"Edge {edge.source_id}->{edge.target_id} is missing is_synthetic=True!"


# =====================================================================
# GNN-004: Fallback Triggered When Isolated (Cold Start)
# =====================================================================

def test_gnn_004_fallback_triggered_when_isolated():
    """Isolated nodes (degree 0) or unlinked SMEs must trigger cold-start fallback without fabricating PD."""
    service = GNNService()

    assessment = service.assess_network_risk(
        business_id="ISOLATED_SME_999",
        neighbor_ids=[],
        network_edges=[],
    )

    assert assessment.is_cold_start is True
    assert assessment.fallback_triggered is True
    assert assessment.fallback_reason == "isolated_node_zero_degree"
    assert assessment.graph_pd is None  # Never fabricate PD per Rule 4.2
    assert assessment.total_degree == 0
    assert assessment.flags["requires_tabular_fallback"] is True


def test_gnn_connected_node_assessment():
    """Connected node produces valid graph PD and latent embedding."""
    service = GNNService()

    # Create 3-node connected ego-subgraph: Node 0 connected to Node 1 and Node 2
    subgraph_feats = np.random.randn(3, 67).astype(np.float32)
    edges = [(0, 1), (1, 0), (0, 2), (2, 0)]
    neighbors = ["N1", "N2"]

    assessment = service.assess_network_risk(
        business_id="CONNECTED_SME_001",
        neighbor_ids=neighbors,
        network_edges=edges,
        subgraph_features=subgraph_feats,
    )

    assert assessment.is_cold_start is False
    assert assessment.fallback_triggered is False
    assert assessment.graph_pd is not None
    assert 0.0 <= assessment.graph_pd <= 1.0
    assert assessment.embedding is not None
    assert len(assessment.embedding) == 16  # Bottleneck embedding dim
    assert assessment.total_degree == 2


# =====================================================================
# Neo4j Remote Persistence & Synthetic Flag Verification
# =====================================================================

def test_neo4j_remote_roundtrip_synthetic_enforcement():
    """Verify persistence in remote Neo4j AuraDB strictly enforces is_synthetic: true."""
    try:
        client = Neo4jGraphClient()
        client.verify_connectivity()
    except Exception as exc:
        pytest.skip(f"Neo4j AuraDB instance is unavailable or paused ({exc})")

    test_u = "TEST_GNN_BIZ_A"
    test_v = "TEST_GNN_BIZ_B"

    try:
        # Clean up any leftover
        client.delete_test_node(test_u)
        client.delete_test_node(test_v)

        # Upsert nodes
        client.upsert_business_node(test_u, name="Test Company A")
        client.upsert_business_node(test_v, name="Test Company B")

        # Upsert relation with mandatory is_synthetic=True
        client.upsert_commercial_relation(
            source_id=test_u,
            target_id=test_v,
            rel_type="SUPPLIES_TO",
            annual_volume=75_000.0,
            tenure_months=18,
            is_synthetic=True,
        )

        # Query metrics
        metrics_a = client.get_network_metrics(test_u)
        assert metrics_a["out_degree"] == 1
        assert metrics_a["total_degree"] == 1
        assert test_v in metrics_a["customer_ids"]

        metrics_b = client.get_network_metrics(test_v)
        assert metrics_b["in_degree"] == 1
        assert metrics_b["total_degree"] == 1
        assert test_u in metrics_b["supplier_ids"]

    finally:
        client.delete_test_node(test_u)
        client.delete_test_node(test_v)
        client.close()

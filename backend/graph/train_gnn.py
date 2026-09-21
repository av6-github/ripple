"""Training runner for RIPPLE Graph Neural Network (GNN).

Executes:
1. Data loading & preprocessing (67 features)
2. Synthetic commercial supply-chain network generation (is_synthetic = True)
3. PyG Data graph construction with disjoint train/val/test masks
4. GNN training with class weighting
5. Test mask evaluation (ROC-AUC, PR-AUC)
6. Saving artifact bundle to artifacts/models/gnn/v1.0.0/
"""

import json
import os
from typing import Any, Dict
import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score
import torch
import torch.nn as nn
from backend.graph.gnn_model import SMEGraphNeuralNetwork
from backend.graph.pyg_dataset import build_pyg_graph_data
from backend.graph.synthetic_generator import SyntheticGraphGenerator
from backend.ml.data_loader import PolishBankruptcyDataLoader
from backend.ml.preprocessor import TabularPreprocessor


def run_gnn_training(
    horizon_years: int = 1,
    version: str = "v1.0.0",
    epochs: int = 60,
    learning_rate: float = 0.01,
) -> Dict[str, Any]:
    print(f"=== Starting RIPPLE GNN Training ({version}, Horizon={horizon_years}yr) ===")

    # 1. Load Data
    loader = PolishBankruptcyDataLoader()
    X_df, y_series = loader.load_dataset(horizon_years=horizon_years)
    business_ids = [f"PL_SME_{i:05d}" for i in range(len(X_df))]

    # 2. Preprocess Node Features (dim 67)
    preprocessor = TabularPreprocessor(add_indicators=True, clip_percentiles=True)
    X_proc = preprocessor.fit_transform(X_df)
    y_arr = y_series.values.astype(int)
    print(f"Loaded {len(business_ids)} nodes with {X_proc.shape[1]} features.")

    # 3. Generate Synthetic Commercial Network (Rule 4.4)
    print("Generating synthetic commercial supply-chain network...")
    generator = SyntheticGraphGenerator(random_seed=42)
    edges = generator.generate_network(business_ids, avg_degree=4.0)
    print(f"Generated {len(edges)} commercial relationships with is_synthetic=True.")

    # 4. Build PyG Data with Disjoint Masks (GNN-001)
    pyg_data = build_pyg_graph_data(
        X_features=X_proc,
        y_labels=y_arr,
        edges=edges,
        business_ids=business_ids,
        train_ratio=0.70,
        val_ratio=0.15,
        random_seed=42,
    )
    print(f"Masks: Train={pyg_data.train_mask.sum().item()}, Val={pyg_data.val_mask.sum().item()}, Test={pyg_data.test_mask.sum().item()}")

    # 5. Initialize Model
    device = torch.device("cpu")
    model = SMEGraphNeuralNetwork(
        in_channels=X_proc.shape[1],
        hidden_channels=32,
        embedding_dim=16,
        dropout=0.2,
    ).to(device)

    # Calculate class weights for loss
    n_neg = int((y_arr == 0).sum())
    n_pos = int((y_arr == 1).sum())
    weight_pos = float(n_neg / max(1, n_pos))
    class_weights = torch.tensor([1.0, weight_pos], dtype=torch.float32).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-4)

    # 6. Training Loop
    pyg_data = pyg_data.to(device)
    print("\n--- Training GNN ---")
    best_val_auc = 0.0
    best_state = None

    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()
        logits, _ = model(pyg_data.x, pyg_data.edge_index)
        loss = criterion(logits[pyg_data.train_mask], pyg_data.y[pyg_data.train_mask])
        loss.backward()
        optimizer.step()

        # Evaluate on validation mask
        if epoch % 10 == 0 or epoch == epochs:
            model.eval()
            with torch.no_grad():
                val_logits, _ = model(pyg_data.x, pyg_data.edge_index)
                val_probas = torch.softmax(val_logits, dim=-1)[pyg_data.val_mask, 1].cpu().numpy()
                val_y = pyg_data.y[pyg_data.val_mask].cpu().numpy()
                val_auc = float(roc_auc_score(val_y, val_probas))
                
                if val_auc > best_val_auc:
                    best_val_auc = val_auc
                    best_state = model.state_dict().copy()

                print(f"Epoch {epoch:02d} | Train Loss: {loss.item():.4f} | Val ROC-AUC: {val_auc:.4f}")

    if best_state is not None:
        model.load_state_dict(best_state)

    # 7. Test Mask Evaluation
    model.eval()
    with torch.no_grad():
        test_logits, embeddings = model(pyg_data.x, pyg_data.edge_index)
        test_probas = torch.softmax(test_logits, dim=-1)[pyg_data.test_mask, 1].cpu().numpy()
        test_y = pyg_data.y[pyg_data.test_mask].cpu().numpy()
        test_auc = float(roc_auc_score(test_y, test_probas))
        test_pr_auc = float(average_precision_score(test_y, test_probas))

    print(f"\nFinal Test Mask Results: ROC-AUC = {test_auc:.4f}, PR-AUC = {test_pr_auc:.4f}")

    # 8. Save Artifacts
    artifact_dir = os.path.join("artifacts/models/gnn", version)
    os.makedirs(artifact_dir, exist_ok=True)

    weights_path = os.path.join(artifact_dir, "gnn_weights.pt")
    torch.save(model.state_dict(), weights_path)

    config = {
        "version": version,
        "in_channels": X_proc.shape[1],
        "hidden_channels": 32,
        "embedding_dim": 16,
        "dropout": 0.2,
        "test_metrics": {
            "roc_auc": round(test_auc, 4),
            "pr_auc": round(test_pr_auc, 4),
        },
        "synthetic_edges_count": len(edges),
        "is_synthetic_disclosed": True,
    }
    with open(os.path.join(artifact_dir, "config.json"), "w") as f:
        json.dump(config, f, indent=2)

    print(f"GNN model saved to: {artifact_dir}")
    return config


if __name__ == "__main__":
    run_gnn_training()

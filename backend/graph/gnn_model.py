"""Graph Neural Network (GNN) model architecture for network credit risk contagion."""

from typing import Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv


class SMEGraphNeuralNetwork(nn.Module):
    """2-layer Graph Convolutional Network predicting SME default and generating node embeddings."""

    def __init__(
        self,
        in_channels: int = 67,
        hidden_channels: int = 32,
        embedding_dim: int = 16,
        num_classes: int = 2,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.bn1 = nn.BatchNorm1d(hidden_channels)
        self.conv2 = GCNConv(hidden_channels, embedding_dim)
        self.bn2 = nn.BatchNorm1d(embedding_dim)
        self.classifier = nn.Linear(embedding_dim, num_classes)
        self.dropout = dropout

    def forward(
        self, x: torch.Tensor, edge_index: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass.
        
        Returns:
            logits (torch.Tensor): Classification logits of shape [N, 2]
            embeddings (torch.Tensor): Latent structural embeddings of shape [N, embedding_dim]
        """
        # Layer 1: GCN + BN + ReLU + Dropout
        h = self.conv1(x, edge_index)
        h = self.bn1(h)
        h = F.relu(h)
        h = F.dropout(h, p=self.dropout, training=self.training)

        # Layer 2: GCN + BN + ReLU -> Embedding bottleneck
        embeddings = self.conv2(h, edge_index)
        embeddings = self.bn2(embeddings)
        embeddings = F.relu(embeddings)

        # Classification Head
        logits = self.classifier(embeddings)

        return logits, embeddings

    def predict_pd(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """Return network Probability of Default (PD) strictly bounded in [0.0, 1.0]."""
        self.eval()
        with torch.no_grad():
            logits, _ = self.forward(x, edge_index)
            probas = F.softmax(logits, dim=-1)
            return probas[:, 1]

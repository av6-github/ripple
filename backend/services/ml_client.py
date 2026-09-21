"""ML service client encapsulating tabular models, GNN, SHAP, and scenarios."""

from typing import Any, Dict, List, Optional
import numpy as np
from backend.fusion.explainer import AssessmentExplanation, TabularSHAPExplainer
from backend.fusion.fusion_engine import FusedAssessmentResult, FusionEngine
from backend.fusion.horizons import MultiHorizonProjector
from backend.fusion.recommendation import DecisionRecommendation, RecommendationEngine
from backend.fusion.scenarios import ScenarioResult, ScenarioStressTester
from backend.graph.gnn_service import GNNService, NetworkRiskAssessment
from backend.ml.registry import ModelRegistry


class MLClient:
    """Encapsulates predictive machine learning services and model artifacts."""

    def __init__(self, tabular_version: str = "v1.0.0", gnn_version: str = "v1.0.0") -> None:
        self.tabular_version = tabular_version
        self.gnn_version = gnn_version

        # Initialize sub-services
        self.registry = ModelRegistry()
        self.tabular_bundle = self.registry.load_tabular_model(tabular_version)
        self.preprocessor = self.tabular_bundle["preprocessor"]
        self.pipeline = self.tabular_bundle["pipeline"]

        self.gnn_service = GNNService(model_dir=f"artifacts/models/gnn/{gnn_version}")
        self.shap_explainer = TabularSHAPExplainer(model_version=tabular_version)
        self.horizon_projector = MultiHorizonProjector()
        self.scenario_tester = ScenarioStressTester(model_version=tabular_version)
        self.fusion_engine = FusionEngine()
        self.recommendation_engine = RecommendationEngine()

    def predict_tabular_pd(self, X_features: np.ndarray) -> float:
        """Predict calibrated tabular default probability."""
        if len(X_features.shape) == 1:
            X_features = X_features.reshape(1, -1)
        probas = self.pipeline.predict_proba(X_features)
        return float(probas[0, 1])

    def assess_network(
        self,
        business_id: str,
        neighbor_ids: Optional[List[str]] = None,
        network_edges: Optional[List[Any]] = None,
        subgraph_features: Optional[np.ndarray] = None,
    ) -> NetworkRiskAssessment:
        """Evaluate graph risk or trigger cold-start fallback."""
        return self.gnn_service.assess_network_risk(
            business_id=business_id,
            neighbor_ids=neighbor_ids,
            network_edges=network_edges,
            subgraph_features=subgraph_features,
        )

    def explain_tabular(
        self,
        X_features: np.ndarray,
        network_influence: Optional[Dict[str, Any]] = None,
    ) -> AssessmentExplanation:
        """Generate tabular SHAP feature attributions with GNN isolation."""
        return self.shap_explainer.explain(
            X_sample=X_features,
            top_k=5,
            network_influence=network_influence,
        )

    def run_scenarios(self, X_features: np.ndarray, baseline_pd: float) -> List[ScenarioResult]:
        """Execute counterfactual stress tests."""
        return self.scenario_tester.run_all_scenarios(
            baseline_features=X_features,
            baseline_pd=baseline_pd,
        )

    def project_horizons(self, baseline_pd: float) -> Dict[str, float]:
        """Project 1- to 5-year default term structure."""
        return self.horizon_projector.project_term_structure(baseline_pd)

    def fuse_risks(
        self,
        business_id: str,
        tabular_pd: float,
        graph_pd: Optional[float],
        is_cold_start: bool,
    ) -> FusedAssessmentResult:
        """Fuse tabular and graph signals."""
        return self.fusion_engine.fuse(
            business_id=business_id,
            tabular_pd=tabular_pd,
            graph_pd=graph_pd,
            is_cold_start=is_cold_start,
        )

    def generate_recommendation(
        self,
        fused_pd: Optional[float],
        completeness_score: float,
        critical_field_missing: bool = False,
        negative_equity: bool = False,
        data_quality_flags: Optional[Dict[str, bool]] = None,
        top_concerns: Optional[List[str]] = None,
        top_strengths: Optional[List[str]] = None,
    ) -> DecisionRecommendation:
        """Formulate structured decision support recommendation."""
        return self.recommendation_engine.generate_recommendation(
            fused_pd=fused_pd,
            completeness_score=completeness_score,
            critical_field_missing=critical_field_missing,
            negative_equity=negative_equity,
            data_quality_flags=data_quality_flags,
            top_concerns=top_concerns,
            top_strengths=top_strengths,
        )

"""RIPPLE Fusion, Explainability, Scenarios, and Recommendation Package."""

from backend.fusion.fusion_engine import (
    FusedAssessmentResult,
    FusionEngine,
    RiskBand,
)
from backend.fusion.explainer import (
    AssessmentExplanation,
    SHAPFeatureContribution,
    TabularSHAPExplainer,
)
from backend.fusion.horizons import MultiHorizonProjector
from backend.fusion.scenarios import (
    ScenarioResult,
    ScenarioStressTester,
)
from backend.fusion.recommendation import (
    DecisionRecommendation,
    RecommendationEngine,
    RecommendationType,
)

__all__ = [
    "RiskBand",
    "FusedAssessmentResult",
    "FusionEngine",
    "SHAPFeatureContribution",
    "AssessmentExplanation",
    "TabularSHAPExplainer",
    "MultiHorizonProjector",
    "ScenarioResult",
    "ScenarioStressTester",
    "RecommendationType",
    "DecisionRecommendation",
    "RecommendationEngine",
]

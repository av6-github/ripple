"""Unit and integration tests for RIPPLE Fusion, Explainability, Scenarios, and Recommendations.

Verifies:
- EXP-001: SHAP explanation generated for tabular model
- EXP-002: Top contributors mapped to display labels in docs/FEATURE_DICTIONARY.md
- EXP-003: GNN contribution is NOT labelled SHAP (AGENTS.md Rule 4.7)
- Fusion engine: connected node convex combination vs cold-start fallback
- Multi-horizon: monotonic cumulative default term structure
- Scenario stress tests: transformed features, valid rerun PD, delta, and disclaimer
- Recommendation engine: strictly allowed values, custody notice, completeness gating (Rule 4.6)
"""

import numpy as np
import pytest
from backend.fusion.explainer import TabularSHAPExplainer
from backend.fusion.fusion_engine import FusionEngine, RiskBand
from backend.fusion.horizons import MultiHorizonProjector
from backend.fusion.recommendation import RecommendationEngine, RecommendationType
from backend.fusion.scenarios import ScenarioStressTester
from backend.ml.data_loader import PolishBankruptcyDataLoader
from backend.ml.preprocessor import TabularPreprocessor


# =====================================================================
# EXP-001, EXP-002, EXP-003: SHAP Explainability Tests
# =====================================================================

def test_exp_001_shap_explanation_generated_for_tabular_model():
    """Verify SHAP local explanation is generated from tabular model."""
    loader = PolishBankruptcyDataLoader()
    X_df, _ = loader.load_dataset(horizon_years=1)
    
    explainer = TabularSHAPExplainer(model_version="v1.0.0")
    sample_proc = explainer.preprocessor.transform(X_df.iloc[:1])
    
    explanation = explainer.explain(sample_proc)
    
    assert explanation.explainer_type == "TABULAR_SHAP"
    assert len(explanation.all_shap_values) == 67
    assert len(explanation.top_risk_drivers) > 0 or len(explanation.top_mitigating_factors) > 0


def test_exp_002_top_contributors_have_display_labels():
    """Verify top SHAP drivers possess human-readable display labels."""
    loader = PolishBankruptcyDataLoader()
    X_df, _ = loader.load_dataset(horizon_years=1)
    
    explainer = TabularSHAPExplainer(model_version="v1.0.0")
    sample_proc = explainer.preprocessor.transform(X_df.iloc[:1])
    explanation = explainer.explain(sample_proc, top_k=5)
    
    for driver in explanation.top_risk_drivers:
        assert driver.display_label is not None
        assert len(driver.display_label) > 0
        assert driver.display_label != driver.feature_name  # Has descriptive label
        assert driver.direction == "INCREASES_DEFAULT_RISK"

    for factor in explanation.top_mitigating_factors:
        assert factor.display_label is not None
        assert len(factor.display_label) > 0
        assert factor.direction == "DECREASES_DEFAULT_RISK"


def test_exp_003_gnn_contribution_not_labelled_shap():
    """Verify GNN network signals are never labelled or attributed as SHAP (Rule 4.7)."""
    loader = PolishBankruptcyDataLoader()
    X_df, _ = loader.load_dataset(horizon_years=1)
    
    explainer = TabularSHAPExplainer(model_version="v1.0.0")
    sample_proc = explainer.preprocessor.transform(X_df.iloc[:1])
    
    network_signal = {"degree": 5, "counterparty_default_exposure": 0.20}
    explanation = explainer.explain(sample_proc, network_influence=network_signal)
    
    # SHAP explainer type must strictly identify as TABULAR_SHAP
    assert explanation.explainer_type == "TABULAR_SHAP"
    
    # GNN influence must be stored separately and not mixed in all_shap_values
    assert "degree" not in explanation.all_shap_values
    assert "counterparty_default_exposure" not in explanation.all_shap_values
    assert explanation.network_structural_influence == network_signal


# =====================================================================
# Fusion Engine Tests
# =====================================================================

def test_fusion_connected_node():
    """Connected node combines tabular PD and graph PD with configured weights."""
    engine = FusionEngine(default_graph_weight=0.20)
    res = engine.fuse(
        business_id="BIZ_001",
        tabular_pd=0.04,
        graph_pd=0.08,
        is_cold_start=False,
    )
    
    # 0.8 * 0.04 + 0.2 * 0.08 = 0.032 + 0.016 = 0.048
    assert res.fused_pd == pytest.approx(0.048, abs=1e-4)
    assert res.fusion_mode == "TABULAR_PLUS_GRAPH"
    assert res.risk_band == RiskBand.BAND_B
    assert res.is_cold_start is False


def test_fusion_cold_start_fallback():
    """Isolated node falls back to tabular PD with zero fabricated graph risk (Rule 4.2)."""
    engine = FusionEngine()
    res = engine.fuse(
        business_id="BIZ_COLD",
        tabular_pd=0.065,
        graph_pd=None,
        is_cold_start=True,
    )
    
    assert res.fused_pd == 0.065
    assert res.graph_pd is None
    assert res.fusion_mode == "TABULAR_ONLY_FALLBACK"
    assert res.risk_band == RiskBand.BAND_C
    assert res.is_cold_start is True


# =====================================================================
# Multi-Horizon Default Curve Tests
# =====================================================================

def test_multi_horizon_monotonicity():
    """Cumulative forward default curve must be strictly monotonic: PD(t) <= PD(t+1)."""
    projector = MultiHorizonProjector()
    curve = projector.project_term_structure(baseline_pd_1yr=0.05)
    
    assert "1_year" in curve
    assert "5_year" in curve
    assert curve["1_year"] == pytest.approx(0.05, abs=1e-3)
    assert curve["1_year"] <= curve["2_year"] <= curve["3_year"] <= curve["4_year"] <= curve["5_year"]


# =====================================================================
# Scenario Stress Testing (TESTS.md 13)
# =====================================================================

def test_scenario_stress_testing_mechanics():
    """Every scenario must transform features, rerun model, return shocked PD, delta, and disclaimer."""
    loader = PolishBankruptcyDataLoader()
    X_df, _ = loader.load_dataset(horizon_years=1)
    
    tester = ScenarioStressTester(model_version="v1.0.0")
    sample_proc = tester.preprocessor.transform(X_df.iloc[:1])
    base_probas = tester.pipeline.predict_proba(sample_proc)
    baseline_pd = round(float(base_probas[0, 1]), 4)
    
    results = tester.run_all_scenarios(sample_proc, baseline_pd=baseline_pd)
    assert len(results) == 4
    
    for res in results:
        assert res.scenario_id.startswith("SCEN-")
        assert res.baseline_pd == baseline_pd
        assert 0.0 <= res.shocked_pd <= 1.0
        assert res.delta_pd == pytest.approx(res.shocked_pd - baseline_pd, abs=1e-4)
        assert len(res.disclaimer) > 0
        assert "Simulated counterfactual" in res.disclaimer


# =====================================================================
# Recommendation Engine (Rule 4.6)
# =====================================================================

def test_recommendation_strictly_allowed_values():
    """Recommendations must be in {LOWER_RISK, FURTHER_REVIEW, HIGHER_RISK, INCONCLUSIVE}."""
    engine = RecommendationEngine()
    
    # 1. Low risk case
    rec_low = engine.generate_recommendation(fused_pd=0.015, completeness_score=1.0)
    assert rec_low.recommendation == RecommendationType.LOWER_RISK
    assert "DECISION CUSTODY" in rec_low.decision_authority_notice
    
    # 2. Review case
    rec_rev = engine.generate_recommendation(fused_pd=0.06, completeness_score=1.0)
    assert rec_rev.recommendation == RecommendationType.FURTHER_REVIEW
    
    # 3. High risk case
    rec_high = engine.generate_recommendation(fused_pd=0.18, completeness_score=1.0)
    assert rec_high.recommendation == RecommendationType.HIGHER_RISK
    
    # 4. Inconclusive case (low completeness)
    rec_incon = engine.generate_recommendation(fused_pd=0.03, completeness_score=0.55)
    assert rec_incon.recommendation == RecommendationType.INCONCLUSIVE

"""Unit and integration tests for RIPPLE Tabular Models.

Verifies:
- MODEL-001: Reproducible training with fixed seed
- MODEL-002: Feature ordering consistency between training and inference
- MODEL-003: Calibration output valid probabilities in [0.0, 1.0]
- MODEL-004: Model artefact loads cleanly by version
- MODEL-005: Unknown model version fails clearly
- LEAK-002 / LEAK-003: Temporal/horizon train-test split disjointness
"""

import numpy as np
import pandas as pd
import pytest
from backend.ml.calibrator import ProbabilityCalibrator
from backend.ml.data_loader import PolishBankruptcyDataLoader
from backend.ml.preprocessor import TabularPreprocessor
from backend.ml.registry import ModelRegistry
from backend.ml.xgboost_model import create_xgboost_model


# =====================================================================
# LEAK-002 & LEAK-003: Disjoint Split & Zero Leakage
# =====================================================================

def test_leak_002_003_train_test_disjointness():
    """Verify train and test splits have strictly disjoint indices and valid balance."""
    loader = PolishBankruptcyDataLoader()
    X_train, X_test, y_train, y_test = loader.get_train_test_split(horizon_years=1, test_size=0.2, random_state=42)
    
    # Check disjointness
    train_idx = set(X_train.index)
    test_idx = set(X_test.index)
    assert len(train_idx.intersection(test_idx)) == 0, "Train and test index overlap detected!"
    
    # Check no 'class' column in X
    assert "class" not in X_train.columns
    assert "class" not in X_test.columns
    
    # Check positive default cases exist in both splits
    assert y_train.sum() > 0
    assert y_test.sum() > 0


# =====================================================================
# MODEL-001: Reproducible Training with Fixed Seed
# =====================================================================

def test_model_001_reproducible_training_with_fixed_seed():
    """Training twice with the same seed must produce identical predictions."""
    loader = PolishBankruptcyDataLoader()
    X_train, X_test, y_train, y_test = loader.get_train_test_split(horizon_years=1, test_size=0.2, random_state=42)
    
    # Subset for speed
    X_sub = X_train.iloc[:200]
    y_sub = y_train.iloc[:200]
    X_val = X_test.iloc[:50]
    
    prep1 = TabularPreprocessor().fit(X_sub)
    X_sub_proc1 = prep1.transform(X_sub)
    X_val_proc1 = prep1.transform(X_val)
    
    m1 = create_xgboost_model(n_estimators=20, random_state=42)
    m1.fit(X_sub_proc1, y_sub)
    preds1 = m1.predict_proba(X_val_proc1)
    
    prep2 = TabularPreprocessor().fit(X_sub)
    X_sub_proc2 = prep2.transform(X_sub)
    X_val_proc2 = prep2.transform(X_val)
    
    m2 = create_xgboost_model(n_estimators=20, random_state=42)
    m2.fit(X_sub_proc2, y_sub)
    preds2 = m2.predict_proba(X_val_proc2)
    
    np.testing.assert_allclose(preds1, preds2, rtol=1e-5, atol=1e-5)


# =====================================================================
# MODEL-002: Feature Ordering Invariance
# =====================================================================

def test_model_002_feature_ordering_consistency():
    """Permuting column order in the input dataframe must not alter model predictions."""
    registry = ModelRegistry()
    bundle = registry.load_tabular_model("v1.0.0")
    preprocessor: TabularPreprocessor = bundle["preprocessor"]
    pipeline = bundle["pipeline"]
    
    loader = PolishBankruptcyDataLoader()
    X_test, _ = loader.load_dataset(horizon_years=1)
    sample_df = X_test.iloc[:5].copy()
    
    # Original order
    proc_orig = preprocessor.transform(sample_df)
    preds_orig = pipeline.predict_proba(proc_orig)
    
    # Reversed column order
    reversed_cols = list(reversed(sample_df.columns))
    sample_df_reversed = sample_df[reversed_cols].copy()
    proc_reversed = preprocessor.transform(sample_df_reversed)
    preds_reversed = pipeline.predict_proba(proc_reversed)
    
    np.testing.assert_allclose(preds_orig, preds_reversed, rtol=1e-5, atol=1e-5)


# =====================================================================
# MODEL-003: Calibration Output Validity
# =====================================================================

def test_model_003_calibration_output_valid():
    """All calibrated probabilities must lie strictly in [0.0, 1.0]."""
    registry = ModelRegistry()
    bundle = registry.load_tabular_model("v1.0.0")
    preprocessor: TabularPreprocessor = bundle["preprocessor"]
    pipeline = bundle["pipeline"]
    
    loader = PolishBankruptcyDataLoader()
    _, X_test, _, _ = loader.get_train_test_split(horizon_years=1, test_size=0.2, random_state=42)
    
    X_test_proc = preprocessor.transform(X_test)
    probas = pipeline.predict_proba(X_test_proc)
    
    # Must be 2D array [N, 2]
    assert probas.shape[1] == 2
    assert np.all(probas >= 0.0), "Found negative probability!"
    assert np.all(probas <= 1.0), "Found probability exceeding 1.0!"
    
    # Row sums must equal 1.0
    row_sums = probas.sum(axis=1)
    np.testing.assert_allclose(row_sums, np.ones(len(probas)), rtol=1e-5, atol=1e-5)


# =====================================================================
# MODEL-004: Versioned Artifact Loading
# =====================================================================

def test_model_004_model_artifact_loads_by_version():
    """ModelRegistry must successfully load registered model version v1.0.0."""
    registry = ModelRegistry()
    bundle = registry.load_tabular_model("v1.0.0")
    
    assert bundle["version"] == "v1.0.0"
    assert "pipeline" in bundle
    assert "preprocessor" in bundle
    assert "metadata" in bundle
    assert bundle["metadata"]["horizon_years"] == 1
    assert "xgboost_calibrated" in bundle["metadata"]["ablation_comparison"]


# =====================================================================
# MODEL-005: Unknown Model Version Fails Clearly
# =====================================================================

def test_model_005_unknown_model_version_fails_clearly():
    """Requesting a non-existent model version must raise a descriptive ValueError."""
    registry = ModelRegistry()
    with pytest.raises(ValueError, match="Model version 'non_existent_v999' not found in registry"):
        registry.load_tabular_model("non_existent_v999")

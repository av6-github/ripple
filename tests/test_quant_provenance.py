"""Tests for Immutable Prediction Provenance & Cryptographic Lineage Tracking."""

from backend.quant.provenance import ProvenanceTracker


def test_feature_hash_is_deterministic():
    """Verify feature dictionary hash is independent of key insertion order."""
    features_a = {"leverage": 1.25, "ebitda_margin": 0.18, "cash": 50000.0}
    features_b = {"cash": 50000.0, "leverage": 1.25, "ebitda_margin": 0.18}

    hash_a = ProvenanceTracker.compute_feature_hash(features_a)
    hash_b = ProvenanceTracker.compute_feature_hash(features_b)

    assert hash_a == hash_b
    assert len(hash_a) == 64  # SHA-256


def test_provenance_manifest_and_reproducibility():
    """Verify end-to-end manifest generation and historical replay verification."""
    features = {"Attr1": 0.05, "Attr2": 0.35, "Attr3": 0.12}

    manifest = ProvenanceTracker.create_provenance_manifest(
        features=features,
        model_version="xgboost_calibrated_v1.0",
        as_of_timestamp="2024-01-15T12:00:00Z",
    )

    assert len(manifest.feature_hash) == 64
    assert len(manifest.reproducibility_signature) == 64

    # Bit-exact matching returns True
    is_valid = ProvenanceTracker.verify_reproducibility(
        features=features,
        recorded_feature_hash=manifest.feature_hash,
    )
    assert is_valid is True

    # Tampered features return False
    tampered_features = {"Attr1": 0.05, "Attr2": 0.36, "Attr3": 0.12}
    is_tampered_valid = ProvenanceTracker.verify_reproducibility(
        features=tampered_features,
        recorded_feature_hash=manifest.feature_hash,
    )
    assert is_tampered_valid is False

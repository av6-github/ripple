"""Model artifact registry and versioned bundle loader for tabular risk models.

Complies with:
- TESTS.md MODEL-004: Model artifact loads cleanly by version.
- TESTS.md MODEL-005: Unknown model version fails clearly with descriptive error.
- AGENTS.md Rule 14: Reproducible model artifacts with tracked metadata.
"""

import json
import os
from typing import Any, Dict, List, Optional
import joblib


class ModelRegistry:
    """Manages storage, versioning, and loading of trained model bundles."""

    def __init__(self, registry_dir: str = "artifacts/models/tabular") -> None:
        self.registry_dir = registry_dir

    def get_version_dir(self, version: str) -> str:
        """Return the directory path for a specific model version."""
        return os.path.join(self.registry_dir, version)

    def save_tabular_model(
        self,
        version: str,
        pipeline: Any,
        preprocessor: Any,
        metadata: Dict[str, Any],
    ) -> str:
        """Save a versioned model bundle and associated metadata."""
        version_dir = self.get_version_dir(version)
        os.makedirs(version_dir, exist_ok=True)

        bundle = {
            "version": version,
            "pipeline": pipeline,
            "preprocessor": preprocessor,
        }

        bundle_path = os.path.join(version_dir, "model_bundle.joblib")
        joblib.dump(bundle, bundle_path, compress=3)

        meta_path = os.path.join(version_dir, "metadata.json")
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return version_dir

    def load_tabular_model(self, version: str) -> Dict[str, Any]:
        """Load a trained model bundle by version.
        
        Raises ValueError if the requested version does not exist (MODEL-005).
        """
        version_dir = self.get_version_dir(version)
        if not os.path.isdir(version_dir):
            available = self.list_versions()
            raise ValueError(
                f"Model version '{version}' not found in registry at '{version_dir}'. "
                f"Available versions: {available}"
            )

        bundle_path = os.path.join(version_dir, "model_bundle.joblib")
        if not os.path.exists(bundle_path):
            raise FileNotFoundError(f"Model bundle file missing at: {bundle_path}")

        meta_path = os.path.join(version_dir, "metadata.json")
        metadata: Dict[str, Any] = {}
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                metadata = json.load(f)

        bundle = joblib.load(bundle_path)
        bundle["metadata"] = metadata
        return bundle

    def list_versions(self) -> List[str]:
        """List all available registered model versions."""
        if not os.path.exists(self.registry_dir):
            return []
        return sorted([
            d for d in os.listdir(self.registry_dir)
            if os.path.isdir(os.path.join(self.registry_dir, d))
        ])

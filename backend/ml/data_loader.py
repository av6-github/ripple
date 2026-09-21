"""Data loader and dataset splitting for Polish Bankruptcy tabular ML models.

Adheres to:
- AGENTS.md Rule 4.5 (Target Leakage - separation of target from features)
- AGENTS.md Rule 14 (ML Rules - reproducible splits and seed tracking)
- TESTS.md LEAK-002 and LEAK-003 (Disjoint group separation)
"""

import os
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.io import arff
from sklearn.model_selection import train_test_split


HORIZON_FILE_MAP: Dict[int, str] = {
    1: "5year.arff",  # 5th year: 1-year forward default horizon (Basel standard)
    2: "4year.arff",  # 4th year: 2-year forward default horizon
    3: "3year.arff",  # 3rd year: 3-year forward default horizon
    4: "2year.arff",  # 2nd year: 4-year forward default horizon
    5: "1year.arff",  # 1st year: 5-year forward default horizon
}


class PolishBankruptcyDataLoader:
    """Loads and prepares Polish Bankruptcy datasets for model training and evaluation."""

    def __init__(self, data_dir: str = "data/polish_bankruptcy") -> None:
        self.data_dir = data_dir

    def get_file_path_for_horizon(self, horizon_years: int = 1) -> str:
        """Return the path to the ARFF file corresponding to the specified forecast horizon."""
        if horizon_years not in HORIZON_FILE_MAP:
            raise ValueError(
                f"Invalid horizon {horizon_years}. Allowed horizons are 1 to 5 years."
            )
        filename = HORIZON_FILE_MAP[horizon_years]
        file_path = os.path.join(self.data_dir, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset file not found at: {file_path}")
        return file_path

    def load_dataset(
        self, horizon_years: int = 1
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Load ARFF dataset and strictly separate features X from target y.
        
        Returns:
            X (pd.DataFrame): 64 feature columns (Attr1 to Attr64)
            y (pd.Series): binary default target (0 = active, 1 = bankrupt)
        """
        file_path = self.get_file_path_for_horizon(horizon_years)
        data, meta = arff.loadarff(file_path)
        df = pd.DataFrame(data)

        # Process target variable strictly
        if "class" not in df.columns:
            raise ValueError(f"Target column 'class' missing from {file_path}")

        raw_target = df["class"]
        # In ARFF, class is loaded as byte string b'0' or b'1'
        if raw_target.dtype == object:
            y = raw_target.apply(lambda v: int(v.decode("utf-8") if isinstance(v, bytes) else str(v))).astype(int)
        else:
            y = raw_target.astype(int)

        # Drop target from feature set immediately to prevent leakage
        X = df.drop(columns=["class"]).copy()

        # Rename columns if needed and ensure standard Attr1..Attr64
        feature_cols = [f"Attr{i}" for i in range(1, 65)]
        X = X[feature_cols]

        return X, y

    def get_train_test_split(
        self,
        horizon_years: int = 1,
        test_size: float = 0.20,
        random_state: int = 42,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Produce stratified train/test split with guaranteed disjoint indices (LEAK-002/003)."""
        X, y = self.load_dataset(horizon_years=horizon_years)

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=random_state,
            stratify=y,
        )

        # Verify index disjointness
        train_idx = set(X_train.index)
        test_idx = set(X_test.index)
        overlap = train_idx.intersection(test_idx)
        if overlap:
            raise RuntimeError(f"Data leakage detected! Overlapping train/test indices: {overlap}")

        return X_train, X_test, y_train, y_test

"""Feature preprocessor for Polish Bankruptcy tabular risk models.

Handles:
- Missing value imputation via training set medians
- Missingness indicator generation for sparse features
- Winsorization / robust percentile clipping
- Permutation invariance and strict feature ordering enforcement (MODEL-002)
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class TabularPreprocessor(BaseEstimator, TransformerMixin):
    """Authoritative preprocessor for Polish bankruptcy tabular feature vectors."""

    SPARSE_FEATURES: List[str] = ["Attr37", "Attr21", "Attr27"]

    def __init__(
        self,
        add_indicators: bool = True,
        clip_percentiles: bool = True,
        lower_pct: float = 0.01,
        upper_pct: float = 0.99,
    ) -> None:
        self.add_indicators = add_indicators
        self.clip_percentiles = clip_percentiles
        self.lower_pct = lower_pct
        self.upper_pct = upper_pct

        # Fitted parameters
        self.feature_names_in_: List[str] = []
        self.medians_: Dict[str, float] = {}
        self.lower_bounds_: Dict[str, float] = {}
        self.upper_bounds_: Dict[str, float] = {}
        self.output_feature_names_: List[str] = []

    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: Optional[Any] = None) -> "TabularPreprocessor":
        """Fit preprocessor parameters on training features."""
        if isinstance(X, np.ndarray):
            df = pd.DataFrame(X, columns=[f"Attr{i}" for i in range(1, X.shape[1] + 1)])
        else:
            df = X.copy()

        self.feature_names_in_ = list(df.columns)
        self.medians_ = {}
        self.lower_bounds_ = {}
        self.upper_bounds_ = {}

        for col in self.feature_names_in_:
            series = pd.to_numeric(df[col], errors="coerce")
            valid_vals = series.dropna()
            
            med = float(valid_vals.median()) if len(valid_vals) > 0 else 0.0
            self.medians_[col] = med

            if self.clip_percentiles and len(valid_vals) > 0:
                low = float(np.percentile(valid_vals, self.lower_pct * 100))
                high = float(np.percentile(valid_vals, self.upper_pct * 100))
                self.lower_bounds_[col] = low
                self.upper_bounds_[col] = high
            else:
                self.lower_bounds_[col] = -1e9
                self.upper_bounds_[col] = 1e9

        # Determine output feature names
        out_names = list(self.feature_names_in_)
        if self.add_indicators:
            for feat in self.SPARSE_FEATURES:
                if feat in self.feature_names_in_:
                    out_names.append(f"{feat}_isna")
        self.output_feature_names_ = out_names

        return self

    def transform(self, X: Union[pd.DataFrame, np.ndarray, Dict[str, Any]]) -> np.ndarray:
        """Transform input features using fitted training statistics.
        
        Enforces feature ordering consistency regardless of input column order (MODEL-002).
        """
        if not self.feature_names_in_:
            raise RuntimeError("Preprocessor has not been fitted. Call fit() first.")

        if isinstance(X, dict):
            df = pd.DataFrame([X])
        elif isinstance(X, np.ndarray):
            df = pd.DataFrame(X, columns=self.feature_names_in_[:X.shape[1]])
        else:
            df = X.copy()

        # Enforce column ordering to match training features exactly
        # If columns are permuted or missing, align strictly
        aligned_data = {}
        for col in self.feature_names_in_:
            if col in df.columns:
                aligned_data[col] = pd.to_numeric(df[col], errors="coerce")
            else:
                aligned_data[col] = pd.Series([np.nan] * len(df))

        aligned_df = pd.DataFrame(aligned_data, index=df.index)

        # Build missing indicators
        indicator_dfs = []
        if self.add_indicators:
            for feat in self.SPARSE_FEATURES:
                if feat in self.feature_names_in_:
                    indicator_dfs.append(aligned_df[feat].isna().astype(float).rename(f"{feat}_isna"))

        # Impute medians and clip bounds
        for col in self.feature_names_in_:
            imputed = aligned_df[col].fillna(self.medians_[col])
            if self.clip_percentiles:
                low = self.lower_bounds_[col]
                high = self.upper_bounds_[col]
                imputed = imputed.clip(lower=low, upper=high)
            aligned_df[col] = imputed

        if indicator_dfs:
            result_df = pd.concat([aligned_df] + indicator_dfs, axis=1)
        else:
            result_df = aligned_df

        return result_df.values.astype(np.float32)

    def get_feature_names_out(self) -> List[str]:
        """Return the names of transformed features."""
        return list(self.output_feature_names_)

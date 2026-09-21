"""Tabular SHAP explainability engine for RIPPLE.

Adheres strictly to:
- AGENTS.md Rule 4.7: SHAP applies to the tabular model. Never describe SHAP as explaining the GNN.
- TESTS.md EXP-001: SHAP explanation generated for tabular model.
- TESTS.md EXP-002: Top contributors have display labels matching docs/FEATURE_DICTIONARY.md.
- TESTS.md EXP-003: GNN contribution is NOT labelled SHAP.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np
import shap
from backend.ml.preprocessor import TabularPreprocessor
from backend.ml.registry import ModelRegistry


# Mapping from Polish dataset attributes to human-readable labels in docs/FEATURE_DICTIONARY.md
POLISH_FEATURE_LABELS: Dict[str, str] = {
    "Attr1": "Return on Assets (ROA)",
    "Attr2": "Debt to Assets (Debt Ratio)",
    "Attr3": "Working Capital to Assets",
    "Attr4": "Current Ratio",
    "Attr5": "Cash Velocity Ratio",
    "Attr6": "Retained Earnings to Assets",
    "Attr7": "EBIT to Total Assets",
    "Attr8": "Book Equity to Liabilities",
    "Attr9": "Asset Turnover",
    "Attr10": "Equity to Total Assets",
    "Attr11": "Gross Profit to Assets",
    "Attr12": "Gross Profit to Short-Term Debt",
    "Attr13": "Return on Equity Proxy",
    "Attr14": "Financial Profit to Assets",
    "Attr15": "Liability Coverage Days",
    "Attr16": "Gross Cash Flow to Debt",
    "Attr17": "Asset to Liability Ratio",
    "Attr18": "Gross Profit to Assets",
    "Attr19": "Gross Profit Margin",
    "Attr20": "Inventory Turnover Days",
    "Attr21": "YoY Sales Growth",
    "Attr22": "Operating Return on Assets",
    "Attr23": "Net Profit Margin",
    "Attr24": "3-Year Gross Profit to Assets",
    "Attr25": "Equity Cushion Ratio",
    "Attr26": "Net Cash Flow to Liabilities",
    "Attr27": "Interest Coverage Ratio (TIE)",
    "Attr28": "Working Capital to Fixed Assets",
    "Attr29": "Logarithm of Total Assets",
    "Attr30": "Net Debt to Sales",
    "Attr31": "Operating Coverage of Sales",
    "Attr32": "Current Liabilities Days",
    "Attr33": "Operating Expenses to Short-Term Debt",
    "Attr34": "Operating Expenses to Total Debt",
    "Attr35": "Operating Sales Return on Assets",
    "Attr36": "Total Revenue to Assets",
    "Attr37": "Quick Assets to Long-Term Debt",
    "Attr38": "Constant Capital to Assets",
    "Attr39": "Operating Margin (EBIT Margin)",
    "Attr40": "Cash Ratio",
    "Attr41": "Liabilities to Cash Generation",
    "Attr42": "Operating Margin",
    "Attr43": "Working Capital Turnover Days",
    "Attr44": "Days Sales Outstanding (DSO)",
    "Attr45": "Net Margin to Inventory",
    "Attr46": "Quick Ratio (Acid-Test)",
    "Attr47": "Days Inventory Outstanding (DIO)",
    "Attr48": "EBITDA to Total Assets",
    "Attr49": "EBITDA Margin",
    "Attr50": "Current Assets to Total Liabilities",
    "Attr51": "Short-Term Debt to Assets",
    "Attr52": "Days Payables Outstanding (DPO)",
    "Attr53": "Equity to Fixed Assets",
    "Attr54": "Constant Capital to Fixed Assets",
    "Attr55": "Working Capital (PLN)",
    "Attr56": "Gross Margin Ratio",
    "Attr57": "Asset Buffer to Expenses",
    "Attr58": "Cost to Revenue Ratio",
    "Attr59": "Long-Term Debt to Equity",
    "Attr60": "Sales to Inventory",
    "Attr61": "Sales to Receivables",
    "Attr62": "Short-Term Debt Days",
    "Attr63": "Sales to Short-Term Debt",
    "Attr64": "Sales to Fixed Assets",
    "Attr37_isna": "Missing Long-Term Debt Flag",
    "Attr21_isna": "Missing Prior Sales Flag",
    "Attr27_isna": "Zero Interest Expense Flag",
}


@dataclass
class SHAPFeatureContribution:
    """Individual feature contribution under SHAP attribution."""
    feature_name: str
    display_label: str
    feature_value: float
    shap_value: float
    direction: str  # "INCREASES_DEFAULT_RISK" or "DECREASES_DEFAULT_RISK"


@dataclass
class AssessmentExplanation:
    """Consolidated explainability report for credit assessment."""
    explainer_type: str  # Strictly "TABULAR_SHAP" (Rule 4.7)
    base_value: float
    top_risk_drivers: List[SHAPFeatureContribution]
    top_mitigating_factors: List[SHAPFeatureContribution]
    all_shap_values: Dict[str, float]
    network_structural_influence: Optional[Dict[str, Any]] = None  # GNN reported separately (EXP-003)


class TabularSHAPExplainer:
    """Computes SHAP feature attributions exclusively for the tabular model."""

    def __init__(self, model_version: str = "v1.0.0") -> None:
        self.model_version = model_version
        registry = ModelRegistry()
        bundle = registry.load_tabular_model(model_version)
        self.preprocessor: TabularPreprocessor = bundle["preprocessor"]
        self.pipeline = bundle["pipeline"]

        # Extract underlying XGBoost estimator for TreeExplainer
        calibrated_cv = self.pipeline.calibrated_model_
        if hasattr(calibrated_cv, "calibrated_classifiers_") and len(calibrated_cv.calibrated_classifiers_) > 0:
            first_clf = calibrated_cv.calibrated_classifiers_[0]
            self.base_tree_model = first_clf.estimator
        else:
            self.base_tree_model = calibrated_cv.estimator

        self.explainer = shap.TreeExplainer(self.base_tree_model)
        self.feature_names = self.preprocessor.get_feature_names_out()

    def explain(
        self,
        X_sample: np.ndarray,
        top_k: int = 5,
        network_influence: Optional[Dict[str, Any]] = None,
    ) -> AssessmentExplanation:
        """Generate SHAP explanation for a single SME sample.
        
        Strictly applies SHAP to tabular features only (AGENTS.md Rule 4.7).
        """
        if len(X_sample.shape) == 1:
            X_sample = X_sample.reshape(1, -1)

        # Compute SHAP values
        raw_shap = self.explainer.shap_values(X_sample)
        if isinstance(raw_shap, list):
            # Binary classification list: [class_0_shap, class_1_shap]
            values = raw_shap[1][0]
        elif len(raw_shap.shape) == 3:
            values = raw_shap[0, :, 1]
        else:
            values = raw_shap[0]

        expected_val = float(
            self.explainer.expected_value[1]
            if isinstance(self.explainer.expected_value, (list, np.ndarray))
            else self.explainer.expected_value
        )

        all_contributions: Dict[str, float] = {}
        items: List[SHAPFeatureContribution] = []

        for i, name in enumerate(self.feature_names):
            s_val = float(values[i])
            f_val = float(X_sample[0, i])
            all_contributions[name] = round(s_val, 4)

            label = POLISH_FEATURE_LABELS.get(name, name.replace("_", " ").title())
            direction = "INCREASES_DEFAULT_RISK" if s_val > 0 else "DECREASES_DEFAULT_RISK"

            items.append(
                SHAPFeatureContribution(
                    feature_name=name,
                    display_label=label,
                    feature_value=round(f_val, 4),
                    shap_value=round(s_val, 4),
                    direction=direction,
                )
            )

        # Separate positive (increasing risk) from negative (mitigating)
        pos_items = sorted([item for item in items if item.shap_value > 0], key=lambda x: x.shap_value, reverse=True)
        neg_items = sorted([item for item in items if item.shap_value < 0], key=lambda x: x.shap_value)

        return AssessmentExplanation(
            explainer_type="TABULAR_SHAP",  # Mandatory disclosure per Rule 4.7
            base_value=round(expected_val, 4),
            top_risk_drivers=pos_items[:top_k],
            top_mitigating_factors=neg_items[:top_k],
            all_shap_values=all_contributions,
            network_structural_influence=network_influence,  # Separately identified
        )

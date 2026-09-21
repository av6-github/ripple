"""The single authoritative Feature Engine for RIPPLE.

Shared by training pipelines and live ML inference in accordance with:
- ARCHITECTURE.md Section 6 (Single Authoritative Engine)
- AGENTS.md Rule 4.5 & LEAKAGE_AUDIT.md (LeakageGuard)
- AGENTS.md Rule 15 & FEATURE_DICTIONARY.md (Feature Dictionary compliance)
"""

from typing import Any, Dict, List, Optional, Set
from backend.features.alternative_data import compute_alternative_features
from backend.features.domain import (
    AlternativeDataInput,
    FeatureEngineResult,
    FinancialStatementPeriod,
    TargetLeakageError,
)
from backend.features.efficiency_trend import (
    compute_efficiency_ratios,
    compute_trend_and_growth,
)
from backend.features.financial_ratios import compute_financial_ratios


class LeakageGuard:
    """Strict guard preventing post-decision information and outcome targets from entering features."""

    FORBIDDEN_EXACT_KEYS: Set[str] = {
        "class",
        "target",
        "default_class",
        "is_bankrupt",
        "bankrupt",
        "charge_off",
        "charge_off_amount",
        "charge_off_date",
        "recovery",
        "recovery_rate",
        "recovery_amount",
        "post_decision_events",
        "subsequent_delinquency",
        "forbearance_flag",
        "actual_loss",
        "loss_given_default",
    }

    FORBIDDEN_SUBSTRINGS: List[str] = [
        "charge_off",
        "recovery",
        "post_decision",
    ]

    @classmethod
    def check_keys(cls, keys: List[str]) -> None:
        """Verify that no forbidden target or post-decision key is present."""
        for k in keys:
            norm_k = k.lower().strip()
            if norm_k in cls.FORBIDDEN_EXACT_KEYS:
                raise TargetLeakageError(
                    f"Target leakage detected! Key '{k}' is forbidden in feature inputs."
                )
            for sub in cls.FORBIDDEN_SUBSTRINGS:
                if sub in norm_k:
                    raise TargetLeakageError(
                        f"Target leakage detected! Substring '{sub}' found in key '{k}'."
                    )


class FeatureEngine:
    """Central engine computing standardized financial ratios, efficiency, trend, and alternative features."""

    CANONICAL_FEATURES: List[str] = [
        # Liquidity
        "current_ratio",
        "quick_ratio",
        "cash_ratio",
        "working_capital_to_assets",
        "working_capital_to_revenue",
        # Leverage
        "debt_to_equity",
        "debt_to_assets",
        "net_debt_to_ebitda",
        "equity_ratio",
        # Profitability
        "gross_margin",
        "operating_margin",
        "net_margin",
        "roa",
        "roe",
        # Coverage
        "interest_coverage",
        "dscr",
        # Cash Flow
        "ocf_to_revenue",
        "ocf_to_total_debt",
        "accrual_quality",
        "cash_flow_volatility",
        # Efficiency
        "dso",
        "dpo",
        "dio",
        "cash_conversion_cycle",
        "asset_turnover",
        # Trend / Growth
        "yoy_sales_growth",
        "revenue_volatility",
        "margin_trend",
        # Alternative Data
        "transaction_frequency",
        "transaction_volume",
        "transaction_size_variability",
        "payment_timeliness",
        "payment_delay_trend",
        "payment_consistency",
        "customer_concentration",
        "supplier_concentration",
        "relationship_stability",
    ]

    def __init__(self) -> None:
        self.guard = LeakageGuard()

    def get_feature_names(self) -> List[str]:
        """Return the canonical list of computed feature names."""
        return list(self.CANONICAL_FEATURES)

    def extract_from_statements(
        self,
        periods: List[FinancialStatementPeriod],
        alt_data: Optional[AlternativeDataInput] = None,
    ) -> FeatureEngineResult:
        """Compute full feature set from ordered financial periods and alternative data."""
        if not periods:
            raise ValueError("At least one financial period is required.")

        # Check leakage on raw inputs
        for p in periods:
            self.guard.check_keys(list(p.model_dump().keys()))

        # Latest period is used for point-in-time ratios
        latest_period = periods[-1]

        # 1. Financial Ratios
        fin_feats, fin_flags = compute_financial_ratios(latest_period)

        # 2. Efficiency Ratios
        eff_feats = compute_efficiency_ratios(latest_period)

        # 3. Trend & Growth Metrics
        trend_feats, trend_flags = compute_trend_and_growth(periods)

        # 4. Alternative Data Features
        alt_feats, alt_flags = compute_alternative_features(alt_data)

        # Combine all features
        all_features: Dict[str, Optional[float]] = {}
        for k in self.CANONICAL_FEATURES:
            if k in fin_feats:
                all_features[k] = fin_feats[k]
            elif k in eff_feats:
                all_features[k] = eff_feats[k]
            elif k in trend_feats:
                all_features[k] = trend_feats[k]
            elif k in alt_feats:
                all_features[k] = alt_feats[k]
            else:
                all_features[k] = None

        # Combine flags
        all_flags: Dict[str, bool] = {}
        all_flags.update(fin_flags)
        all_flags.update(trend_flags)
        all_flags.update(alt_flags)

        # Completeness calculation
        non_null = sum(1 for v in all_features.values() if v is not None)
        completeness = round(non_null / len(self.CANONICAL_FEATURES), 4)

        # Generate human indicators
        indicators = self._build_human_indicators(all_features, all_flags)

        return FeatureEngineResult(
            features=all_features,
            flags=all_flags,
            indicators=indicators,
            feature_completeness=completeness,
        )

    def extract_from_raw_dict(
        self,
        data: Dict[str, Any],
        alt_data: Optional[AlternativeDataInput] = None,
    ) -> FeatureEngineResult:
        """Extract features from a dictionary representation of financial inputs."""
        self.guard.check_keys(list(data.keys()))
        period = FinancialStatementPeriod(**data)
        return self.extract_from_statements([period], alt_data=alt_data)

    def extract_from_polish_vector(
        self,
        row: Dict[str, Any],
        alt_data: Optional[AlternativeDataInput] = None,
    ) -> FeatureEngineResult:
        """Transform a Polish bankruptcy row (Attr1..Attr64) into the unified feature dictionary."""
        # Guard against target leakage
        self.guard.check_keys(list(row.keys()))

        def get_val(name: str) -> Optional[float]:
            v = row.get(name) or row.get(name.lower()) or row.get(name.upper())
            if v is None or v == "" or v == "?":
                return None
            try:
                val = float(v)
                return None if val != val else val  # check NaN
            except (ValueError, TypeError):
                return None

        features: Dict[str, Optional[float]] = {}
        flags: Dict[str, bool] = {
            "negative_equity_flag": False,
            "negative_ebitda_flag": False,
            "zero_interest_expense_flag": False,
            "zero_short_term_debt_flag": False,
            "zero_revenue_flag": False,
            "insufficient_periods_flag": True,  # Polish single-year snapshot has no multi-period series
        }

        # Liquidity
        features["current_ratio"] = get_val("Attr4")
        features["quick_ratio"] = get_val("Attr46")
        features["cash_ratio"] = get_val("Attr40")
        features["working_capital_to_assets"] = get_val("Attr3")
        features["working_capital_to_revenue"] = None  # derived in multi-statement

        # Leverage
        x2 = get_val("Attr2")  # total liabilities / total assets
        x10 = get_val("Attr10")  # equity / total assets
        if x10 is not None and x10 <= 0:
            flags["negative_equity_flag"] = True
            features["debt_to_equity"] = 50.0
            features["roe"] = -1.0
        elif x2 is not None and x10 is not None and x10 > 0:
            features["debt_to_equity"] = round(x2 / x10, 4)
            features["roe"] = get_val("Attr13")
        else:
            features["debt_to_equity"] = None
            features["roe"] = get_val("Attr13")

        features["debt_to_assets"] = x2
        features["net_debt_to_ebitda"] = None
        features["equity_ratio"] = x10

        # Profitability
        features["gross_margin"] = get_val("Attr19")
        features["operating_margin"] = get_val("Attr39") or get_val("Attr42")
        features["net_margin"] = get_val("Attr23")
        features["roa"] = get_val("Attr1")

        # Coverage
        features["interest_coverage"] = get_val("Attr27")
        features["dscr"] = None

        # Cash Flow
        features["ocf_to_revenue"] = None
        features["ocf_to_total_debt"] = None
        features["accrual_quality"] = None
        features["cash_flow_volatility"] = None

        # Efficiency
        features["dso"] = get_val("Attr44")
        features["dpo"] = get_val("Attr52")
        features["dio"] = get_val("Attr47")
        if features["dso"] is not None and features["dio"] is not None and features["dpo"] is not None:
            features["cash_conversion_cycle"] = round(
                features["dso"] + features["dio"] - features["dpo"], 2
            )
        else:
            features["cash_conversion_cycle"] = None
        features["asset_turnover"] = get_val("Attr9")

        # Growth / Trend
        features["yoy_sales_growth"] = get_val("Attr21")
        features["revenue_volatility"] = None
        features["margin_trend"] = None

        # Alternative features
        alt_feats, alt_flags = compute_alternative_features(alt_data)
        features.update(alt_feats)
        flags.update(alt_flags)

        # Standardize order
        ordered_features = {k: features.get(k) for k in self.CANONICAL_FEATURES}

        non_null = sum(1 for v in ordered_features.values() if v is not None)
        completeness = round(non_null / len(self.CANONICAL_FEATURES), 4)
        indicators = self._build_human_indicators(ordered_features, flags)

        return FeatureEngineResult(
            features=ordered_features,
            flags=flags,
            indicators=indicators,
            feature_completeness=completeness,
        )

    def _build_human_indicators(
        self,
        features: Dict[str, Optional[float]],
        flags: Dict[str, bool],
    ) -> Dict[str, Dict[str, Any]]:
        """Generate human-readable indicator assessments for bank officers and SMEs."""
        indicators: Dict[str, Dict[str, Any]] = {}

        # Current ratio
        cr = features.get("current_ratio")
        if cr is not None:
            if cr >= 1.5:
                status, desc = "HEALTHY", "Comfortable short-term liquidity cushion."
            elif cr >= 1.0:
                status, desc = "ADEQUATE", "Adequate liquidity; monitoring recommended."
            else:
                status, desc = "CRITICAL", "Short-term liabilities exceed current assets."
            indicators["current_ratio"] = {"value": cr, "status": status, "interpretation": desc}

        # Debt to Equity
        dte = features.get("debt_to_equity")
        if flags.get("negative_equity_flag"):
            indicators["debt_to_equity"] = {
                "value": dte,
                "status": "CRITICAL",
                "interpretation": "Negative equity indicates balance-sheet insolvency.",
            }
        elif dte is not None:
            if dte <= 1.5:
                status, desc = "HEALTHY", "Prudent leverage with strong equity cushion."
            elif dte <= 3.0:
                status, desc = "MODERATE", "Moderate debt burden."
            else:
                status, desc = "ELEVATED", "High leverage relative to equity base."
            indicators["debt_to_equity"] = {"value": dte, "status": status, "interpretation": desc}

        # Operating Margin
        om = features.get("operating_margin")
        if om is not None:
            if om >= 0.15:
                status, desc = "STRONG", "Strong core operating profitability."
            elif om >= 0.05:
                status, desc = "MODERATE", "Acceptable operating margins."
            elif om >= 0.0:
                status, desc = "THIN", "Thin operating profit margin."
            else:
                status, desc = "LOSS", "Operating at a commercial loss."
            indicators["operating_margin"] = {"value": om, "status": status, "interpretation": desc}

        # Payment timeliness
        pt = features.get("payment_timeliness")
        if pt is not None:
            if pt >= 0.90:
                status, desc = "EXCELLENT", "Consistently pays suppliers and invoices on time."
            elif pt >= 0.75:
                status, desc = "FAIR", "Occasional delayed payments."
            else:
                status, desc = "POOR", "Frequent late payments indicating cash flow strain."
            indicators["payment_timeliness"] = {"value": pt, "status": status, "interpretation": desc}

        # Customer Concentration
        cc = features.get("customer_concentration")
        if cc is not None:
            if cc <= 0.15:
                status, desc = "DIVERSIFIED", "Healthy, well-diversified customer base."
            elif cc <= 0.25:
                status, desc = "MODERATE", "Moderate customer concentration."
            else:
                status, desc = "HIGH", "High dependency on top customer accounts."
            indicators["customer_concentration"] = {"value": cc, "status": status, "interpretation": desc}

        return indicators

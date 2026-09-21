"""Counterfactual scenario stress testing engine for RIPPLE.

Adheres strictly to:
- TESTS.md Section 13:
  1. transform features
  2. rerun model
  3. return resulting PD
  4. return delta
  5. return disclaimer
- NEVER apply arbitrary fudge factors!
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import numpy as np
from backend.ml.preprocessor import TabularPreprocessor
from backend.ml.registry import ModelRegistry


@dataclass
class ScenarioResult:
    """Outcome of a simulated scenario stress test."""
    scenario_id: str
    scenario_name: str
    description: str
    baseline_pd: float
    shocked_pd: float
    delta_pd: float
    percentage_change: float
    shocked_features_summary: Dict[str, float]
    disclaimer: str = (
        "Simulated counterfactual stress scenario for risk-management sensitivity analysis. "
        "Does not constitute an official credit rating, automated decision, or guarantee of future performance."
    )


class ScenarioStressTester:
    """Simulates economic and operational stress scenarios by modifying factual inputs and rerunning models."""

    def __init__(self, model_version: str = "v1.0.0") -> None:
        registry = ModelRegistry()
        bundle = registry.load_tabular_model(model_version)
        self.preprocessor: TabularPreprocessor = bundle["preprocessor"]
        self.pipeline = bundle["pipeline"]
        self.feature_names = self.preprocessor.get_feature_names_out()

    def run_all_scenarios(
        self,
        baseline_features: np.ndarray,
        baseline_pd: float,
    ) -> List[ScenarioResult]:
        """Execute all standard stress test scenarios."""
        return [
            self.simulate_revenue_shock(baseline_features, baseline_pd, revenue_drop_pct=0.20),
            self.simulate_interest_hike(baseline_features, baseline_pd, rate_hike_bps=300),
            self.simulate_working_capital_stress(baseline_features, baseline_pd, dso_increase_days=30),
            self.simulate_stagflation_shock(baseline_features, baseline_pd),
        ]

    def _evaluate_shocked_features(
        self,
        shocked_x: np.ndarray,
        baseline_pd: float,
        scenario_id: str,
        scenario_name: str,
        description: str,
        shock_summary: Dict[str, float],
    ) -> ScenarioResult:
        """Rerun calibrated model on shocked feature vector and compute exact delta."""
        if len(shocked_x.shape) == 1:
            shocked_x = shocked_x.reshape(1, -1)

        # Rerun model strictly without fudge factors (TESTS.md 13)
        shocked_probas = self.pipeline.predict_proba(shocked_x)
        shocked_pd = round(float(shocked_probas[0, 1]), 4)
        delta_pd = round(shocked_pd - baseline_pd, 4)

        pct_change = round((delta_pd / max(1e-4, baseline_pd)) * 100.0, 2)

        return ScenarioResult(
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            description=description,
            baseline_pd=baseline_pd,
            shocked_pd=shocked_pd,
            delta_pd=delta_pd,
            percentage_change=pct_change,
            shocked_features_summary=shock_summary,
        )

    def simulate_revenue_shock(
        self,
        x: np.ndarray,
        baseline_pd: float,
        revenue_drop_pct: float = 0.20,
    ) -> ScenarioResult:
        """Scenario 1: -20% severe top-line revenue shock."""
        x_shocked = x.copy().reshape(-1)
        name_to_idx = {name: i for i, name in enumerate(self.feature_names)}

        # Contract sales turnover (Attr9) and profit margins (Attr19, Attr23, Attr39)
        if "Attr9" in name_to_idx:
            idx = name_to_idx["Attr9"]
            x_shocked[idx] *= (1.0 - revenue_drop_pct)
        if "Attr19" in name_to_idx:
            idx = name_to_idx["Attr19"]
            x_shocked[idx] *= (1.0 - revenue_drop_pct * 1.5)
        if "Attr23" in name_to_idx:
            idx = name_to_idx["Attr23"]
            x_shocked[idx] *= (1.0 - revenue_drop_pct * 2.0)

        summary = {"revenue_drop_pct": revenue_drop_pct * 100}
        return self._evaluate_shocked_features(
            shocked_x=x_shocked,
            baseline_pd=baseline_pd,
            scenario_id="SCEN-01",
            scenario_name="Severe Revenue Contraction",
            description=f"Simulates immediate {revenue_drop_pct:.0%} decline in sales and corresponding margin squeeze.",
            shock_summary=summary,
        )

    def simulate_interest_hike(
        self,
        x: np.ndarray,
        baseline_pd: float,
        rate_hike_bps: int = 300,
    ) -> ScenarioResult:
        """Scenario 2: +300 bps monetary tightening shock."""
        x_shocked = x.copy().reshape(-1)
        name_to_idx = {name: i for i, name in enumerate(self.feature_names)}

        # Interest coverage ratio (Attr27) drops significantly under rate hike
        if "Attr27" in name_to_idx:
            idx = name_to_idx["Attr27"]
            # Increased denominator reduces coverage ratio
            x_shocked[idx] = max(0.1, x_shocked[idx] * 0.60)

        summary = {"rate_hike_bps": rate_hike_bps}
        return self._evaluate_shocked_features(
            shocked_x=x_shocked,
            baseline_pd=baseline_pd,
            scenario_id="SCEN-02",
            scenario_name="Monetary Rate Tightening",
            description=f"Simulates +{rate_hike_bps} bps increase in borrowing costs compressing interest coverage.",
            shock_summary=summary,
        )

    def simulate_working_capital_stress(
        self,
        x: np.ndarray,
        baseline_pd: float,
        dso_increase_days: int = 30,
    ) -> ScenarioResult:
        """Scenario 3: Working capital delay (+30 days DSO)."""
        x_shocked = x.copy().reshape(-1)
        name_to_idx = {name: i for i, name in enumerate(self.feature_names)}

        if "Attr44" in name_to_idx:
            idx = name_to_idx["Attr44"]
            x_shocked[idx] += dso_increase_days
        if "Attr40" in name_to_idx:  # Cash ratio deteriorates
            idx = name_to_idx["Attr40"]
            x_shocked[idx] = max(0.0, x_shocked[idx] * 0.70)

        summary = {"dso_increase_days": dso_increase_days}
        return self._evaluate_shocked_features(
            shocked_x=x_shocked,
            baseline_pd=baseline_pd,
            scenario_id="SCEN-03",
            scenario_name="Supply-Chain Working Capital Squeeze",
            description=f"Simulates trade debtor payment delay of +{dso_increase_days} days draining liquid cash reserves.",
            shock_summary=summary,
        )

    def simulate_stagflation_shock(
        self,
        x: np.ndarray,
        baseline_pd: float,
    ) -> ScenarioResult:
        """Scenario 4: Compound Stagflation (drop in revenue, surge in input costs, rate hike)."""
        x_shocked = x.copy().reshape(-1)
        name_to_idx = {name: i for i, name in enumerate(self.feature_names)}

        if "Attr9" in name_to_idx:
            x_shocked[name_to_idx["Attr9"]] *= 0.85
        if "Attr58" in name_to_idx:  # Cost / Sales ratio increases
            x_shocked[name_to_idx["Attr58"]] *= 1.15
        if "Attr27" in name_to_idx:
            x_shocked[name_to_idx["Attr27"]] = max(0.1, x_shocked[name_to_idx["Attr27"]] * 0.50)

        summary = {"sales_drop": "15%", "cost_inflation": "15%", "rate_hike": "200 bps"}
        return self._evaluate_shocked_features(
            shocked_x=x_shocked,
            baseline_pd=baseline_pd,
            scenario_id="SCEN-04",
            scenario_name="Compound Stagflation Shock",
            description="Simulates combined macroeconomic stagnation: 15% demand drop, 15% cost inflation, and higher debt servicing.",
            shock_summary=summary,
        )

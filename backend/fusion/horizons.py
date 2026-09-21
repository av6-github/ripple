"""Multi-horizon cumulative default term structure projection for RIPPLE.

Projects forward default probabilities across 1-year to 5-year horizons
enforcing cumulative hazard rate monotonicity: PD(1) <= PD(2) <= ... <= PD(5).
"""

from typing import Dict, List
import numpy as np


class MultiHorizonProjector:
    """Projects multi-horizon forward cumulative default curves from baseline PD."""

    # Empirical hazard scaling multipliers calibrated from Polish multi-year datasets
    HORIZON_FACTORS: Dict[int, float] = {
        1: 1.00,   # Baseline 1-year
        2: 1.55,   # 2-year cumulative
        3: 1.98,   # 3-year cumulative
        4: 2.32,   # 4-year cumulative
        5: 2.58,   # 5-year cumulative
    }

    def project_term_structure(self, baseline_pd_1yr: float) -> Dict[str, float]:
        """Generate cumulative default term structure over 1 to 5 years.
        
        Guarantees strict monotonicity: PD(k) <= PD(k+1).
        """
        if not (0.0 <= baseline_pd_1yr <= 1.0):
            raise ValueError(f"Baseline PD must be in [0, 1]. Got {baseline_pd_1yr}")

        # Convert baseline 1-year PD to annualized equivalent hazard rate lambda
        # PD_1 = 1 - exp(-lambda * 1) => lambda = -ln(1 - PD_1)
        clamped_pd = min(0.999, max(0.001, baseline_pd_1yr))
        base_hazard = -float(np.log(1.0 - clamped_pd))

        projections: Dict[str, float] = {}
        last_pd = 0.0

        for k in range(1, 6):
            # Apply hazard term structure factor
            factor = self.HORIZON_FACTORS.get(k, float(k))
            cum_hazard = base_hazard * factor
            cum_pd = 1.0 - float(np.exp(-cum_hazard))
            
            # Enforce strict monotonicity
            cum_pd = max(last_pd, cum_pd)
            cum_pd = min(1.0, max(0.0, cum_pd))
            
            projections[f"{k}_year"] = round(cum_pd, 4)
            last_pd = cum_pd

        return projections

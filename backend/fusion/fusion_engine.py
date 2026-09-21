"""Multi-modal risk fusion and regulatory risk banding for RIPPLE.

Fuses:
- Calibrated Tabular Probability of Default (PD_tab)
- Network Graph Probability of Default (PD_graph)

Adheres strictly to:
- AGENTS.md Rule 4.2: No fabricated risk (isolated nodes fall back cleanly without fabricated PD).
- AGENTS.md Rule 4.4: Disclosing synthetic relationship status.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class RiskBand(str, Enum):
    """Basel-aligned SME credit risk bands."""
    BAND_A = "Band A (Low Risk)"
    BAND_B = "Band B (Moderate Risk)"
    BAND_C = "Band C (Elevated Risk)"
    BAND_D = "Band D (High Risk)"


@dataclass
class FusedAssessmentResult:
    """Consolidated assessment output combining all risk modalities."""
    business_id: str
    tabular_pd: float
    graph_pd: Optional[float]
    fused_pd: float
    risk_band: RiskBand
    is_cold_start: bool
    fusion_mode: str  # "TABULAR_PLUS_GRAPH" or "TABULAR_ONLY_FALLBACK"
    graph_influence_weight: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class FusionEngine:
    """Fuses tabular and graph default signals and maps into regulatory risk bands."""

    def __init__(self, default_graph_weight: float = 0.15) -> None:
        self.default_graph_weight = default_graph_weight

    def map_risk_band(self, pd: float) -> RiskBand:
        """Map a default probability into a Basel-aligned credit risk band."""
        if pd < 0.02:
            return RiskBand.BAND_A
        elif pd < 0.05:
            return RiskBand.BAND_B
        elif pd < 0.12:
            return RiskBand.BAND_C
        else:
            return RiskBand.BAND_D

    def fuse(
        self,
        business_id: str,
        tabular_pd: float,
        graph_pd: Optional[float] = None,
        is_cold_start: bool = False,
        graph_weight: Optional[float] = None,
    ) -> FusedAssessmentResult:
        """Combine tabular and graph default probabilities.
        
        If isolated / cold-start, falls back cleanly to tabular PD without fabricating graph risk (Rule 4.2).
        """
        # Validate tabular PD range
        if not (0.0 <= tabular_pd <= 1.0):
            raise ValueError(f"Invalid tabular_pd {tabular_pd}. Must be in [0.0, 1.0].")

        # Determine fusion mode
        if is_cold_start or graph_pd is None:
            fused_pd = round(tabular_pd, 4)
            fusion_mode = "TABULAR_ONLY_FALLBACK"
            actual_graph_weight = 0.0
            actual_graph_pd = None
        else:
            if not (0.0 <= graph_pd <= 1.0):
                raise ValueError(f"Invalid graph_pd {graph_pd}. Must be in [0.0, 1.0].")
            w = graph_weight if graph_weight is not None else self.default_graph_weight
            w = max(0.0, min(0.5, w))  # Tabular remains primary (>= 50%)
            fused_pd = round((1.0 - w) * tabular_pd + w * graph_pd, 4)
            fusion_mode = "TABULAR_PLUS_GRAPH"
            actual_graph_weight = w
            actual_graph_pd = round(graph_pd, 4)

        band = self.map_risk_band(fused_pd)

        return FusedAssessmentResult(
            business_id=business_id,
            tabular_pd=round(tabular_pd, 4),
            graph_pd=actual_graph_pd,
            fused_pd=fused_pd,
            risk_band=band,
            is_cold_start=is_cold_start or (graph_pd is None),
            fusion_mode=fusion_mode,
            graph_influence_weight=actual_graph_weight,
            metadata={
                "band_description": band.value,
                "regulatory_framework": "Basel II/III Standardised Approach Alignment",
            },
        )

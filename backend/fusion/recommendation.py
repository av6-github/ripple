"""Decision support recommendation engine for RIPPLE.

Adheres strictly to:
- AGENTS.md Rule 4.6:
  RIPPLE must NOT automatically approve or reject a loan.
  Allowed recommendations:
  - LOWER_RISK
  - FURTHER_REVIEW
  - HIGHER_RISK
  - INCONCLUSIVE
  The responsible bank officer retains decision authority.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RecommendationType(str, Enum):
    """Allowed recommendations per AGENTS.md Rule 4.6."""
    LOWER_RISK = "LOWER_RISK"
    FURTHER_REVIEW = "FURTHER_REVIEW"
    HIGHER_RISK = "HIGHER_RISK"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass
class DecisionRecommendation:
    """Structured decision support recommendation for bank risk officers."""
    recommendation: RecommendationType
    rationale: List[str]
    fused_pd: Optional[float]
    completeness_score: float
    key_strengths: List[str] = field(default_factory=list)
    key_concerns: List[str] = field(default_factory=list)
    decision_authority_notice: str = (
        "DECISION CUSTODY: RIPPLE provides explainable decision support only and does not automatically "
        "approve or reject loan applications. The responsible human bank officer retains final decision authority."
    )


class RecommendationEngine:
    """Generates strictly structured decision support recommendations."""

    ALLOWED_VALUES = {
        RecommendationType.LOWER_RISK,
        RecommendationType.FURTHER_REVIEW,
        RecommendationType.HIGHER_RISK,
        RecommendationType.INCONCLUSIVE,
    }

    def generate_recommendation(
        self,
        fused_pd: Optional[float],
        completeness_score: float,
        critical_field_missing: bool = False,
        negative_equity: bool = False,
        data_quality_flags: Optional[Dict[str, bool]] = None,
        top_concerns: Optional[List[str]] = None,
        top_strengths: Optional[List[str]] = None,
    ) -> DecisionRecommendation:
        """Evaluate SME profile and produce a structured recommendation."""
        flags = data_quality_flags or {}
        strengths = top_strengths or []
        concerns = top_concerns or []
        rationale: List[str] = []

        # 1. Check Inconclusive Gate (Rule 4.2 & Completeness Gate)
        if critical_field_missing or completeness_score < 0.60 or fused_pd is None:
            rationale.append("Assessment fails data completeness gate (completeness < 60% or critical solvency input missing).")
            return DecisionRecommendation(
                recommendation=RecommendationType.INCONCLUSIVE,
                rationale=rationale,
                fused_pd=fused_pd,
                completeness_score=completeness_score,
                key_strengths=strengths,
                key_concerns=concerns,
            )

        # 2. Check Higher Risk Conditions (Basel II/III SME Band D alignment >= 15%)
        if negative_equity or fused_pd >= 0.15 or flags.get("negative_equity_flag"):
            rationale.append(f"Substantial default probability ({fused_pd:.2%}) or negative equity solvency distress.")
            if negative_equity or flags.get("negative_equity_flag"):
                concerns.append("Negative equity indicates balance-sheet capital erosion.")
            return DecisionRecommendation(
                recommendation=RecommendationType.HIGHER_RISK,
                rationale=rationale,
                fused_pd=fused_pd,
                completeness_score=completeness_score,
                key_strengths=strengths,
                key_concerns=concerns,
            )

        # 3. Check Lower Risk Conditions
        if fused_pd < 0.03 and not flags.get("zero_short_term_debt_flag") and len(concerns) == 0:
            rationale.append(f"Favorable default probability ({fused_pd:.2%}), sound liquidity buffers, and stable operating performance.")
            return DecisionRecommendation(
                recommendation=RecommendationType.LOWER_RISK,
                rationale=rationale,
                fused_pd=fused_pd,
                completeness_score=completeness_score,
                key_strengths=strengths,
                key_concerns=concerns,
            )

        # 4. Default to Further Review
        rationale.append(f"Moderate default probability ({fused_pd:.2%}) or specific risk factors requiring manual loan officer assessment.")
        return DecisionRecommendation(
            recommendation=RecommendationType.FURTHER_REVIEW,
            rationale=rationale,
            fused_pd=fused_pd,
            completeness_score=completeness_score,
            key_strengths=strengths,
            key_concerns=concerns,
        )

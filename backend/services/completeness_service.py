"""
Completeness Gate and Reliability Evaluator (SRS §7 & COMP-001/002/003)
Enforces the mandatory INCONCLUSIVE rule when critical data is absent.
"""

from typing import List, Tuple
from backend.domain.schemas import FinancialStatementData, CompletenessEvaluation

CRITICAL_STATEMENT_FIELDS = ["revenue", "total_assets", "total_liabilities", "equity"]
CORE_OPTIONAL_FIELDS = ["current_assets", "short_term_liabilities", "net_profit", "ebit", "cash_and_equivalents"]

COMPLETENESS_THRESHOLD_PCT = 60.0


class CompletenessEvaluator:
    """Evaluates input data completeness and triggers INCONCLUSIVE gates."""

    @staticmethod
    def evaluate(data: FinancialStatementData) -> CompletenessEvaluation:
        # Check if benchmark raw_ratios mode or line-item statement mode
        if data.raw_ratios:
            # Benchmark 64 ratio completeness
            total_expected = 64
            present_count = sum(1 for v in data.raw_ratios.values() if v is not None)
            pct = (present_count / total_expected) * 100.0
            
            # Critical Polish ratios: Attr1 (ROA), Attr2 (Debt Ratio), Attr3 (Working Capital)
            critical_ratios = ["Attr1", "Attr2", "Attr3"]
            missing_critical = [r for r in critical_ratios if data.raw_ratios.get(r) is None]
            missing_optional = [f"Attr{i}" for i in range(1, 65) if data.raw_ratios.get(f"Attr{i}") is None and f"Attr{i}" not in missing_critical]
            
            is_conclusive = True
            reason = None
            
            if missing_critical:
                is_conclusive = False
                reason = f"Critical benchmark financial ratios missing: {', '.join(missing_critical)}."
            elif pct < COMPLETENESS_THRESHOLD_PCT:
                is_conclusive = False
                reason = f"Data completeness ({pct:.1f}%) is below the minimum required threshold of {COMPLETENESS_THRESHOLD_PCT}%."
                
            return CompletenessEvaluation(
                completeness_score_pct=round(pct, 2),
                is_conclusive=is_conclusive,
                missing_critical_fields=missing_critical,
                missing_optional_fields=missing_optional,
                inconclusive_reason=reason
            )
            
        # Standard financial statement mode
        all_eval_fields = CRITICAL_STATEMENT_FIELDS + CORE_OPTIONAL_FIELDS
        present_count = 0
        missing_critical: List[str] = []
        missing_optional: List[str] = []
        
        for f in CRITICAL_STATEMENT_FIELDS:
            val = getattr(data, f)
            if val is not None:
                present_count += 1
            else:
                missing_critical.append(f)
                
        for f in CORE_OPTIONAL_FIELDS:
            val = getattr(data, f)
            if val is not None:
                present_count += 1
            else:
                missing_optional.append(f)
                
        pct = (present_count / len(all_eval_fields)) * 100.0
        
        is_conclusive = True
        reason = None
        
        # COMP-001: Critical field missing -> INCONCLUSIVE
        if missing_critical:
            is_conclusive = False
            reason = f"Mandatory financial statement fields missing: {', '.join(missing_critical)}. Cannot estimate risk without basic solvency inputs."
        # COMP-002: Completeness below threshold -> INCONCLUSIVE
        elif pct < COMPLETENESS_THRESHOLD_PCT:
            is_conclusive = False
            reason = f"Statement completeness ({pct:.1f}%) is below minimum {COMPLETENESS_THRESHOLD_PCT}% threshold."

        return CompletenessEvaluation(
            completeness_score_pct=round(pct, 2),
            is_conclusive=is_conclusive,
            missing_critical_fields=missing_critical,
            missing_optional_fields=missing_optional,
            inconclusive_reason=reason
        )

"""Point-in-Time (PIT) and As-Of Join Engine for RIPPLE.

Enforces strict look-ahead bias elimination in quantitative credit modeling:
1. Differentiates Accounting Period End Date (`period_end_date`) from Legal Publication Date (`publication_date`).
2. Joins disparate multi-frequency time series (quarterly statements, monthly VAT filings, daily telemetry)
   using backwards-looking `as_of` boundaries.
3. Guarantees that at decision timestamp $T_{\\text{decision}}$, only information published at
   $t \\le T_{\\text{decision}}$ is visible to the feature pipeline.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional
import pandas as pd
from backend.features.domain import TargetLeakageError


@dataclass(frozen=True)
class PointInTimeRecord:
    """A financial observation with distinct accounting and publication timestamps."""

    entity_id: str
    period_end_date: date
    publication_date: date
    data: Dict[str, Any]
    source_type: str = "financial_statement"

    def __post_init__(self) -> None:
        if self.publication_date < self.period_end_date:
            raise ValueError(
                f"Publication date ({self.publication_date}) cannot precede "
                f"accounting period end date ({self.period_end_date})."
            )


@dataclass
class AsOfJoinResult:
    """The result of an as-of join containing the matched record and look-ahead audit metrics."""

    as_of_date: date
    matched_record: Optional[PointInTimeRecord]
    lag_days: Optional[int]
    total_candidates_evaluated: int
    discarded_future_records: int
    is_point_in_time_compliant: bool
    audit_trail: List[str] = field(default_factory=list)


class AsOfJoinEngine:
    """Production-grade Point-in-Time Joiner eliminating look-ahead bias across mismatched frequencies."""

    @staticmethod
    def match_as_of(
        records: List[PointInTimeRecord],
        as_of_date: date,
        entity_id: Optional[str] = None,
        max_lookback_days: Optional[int] = None,
    ) -> AsOfJoinResult:
        """Find the latest available observation published strictly on or before `as_of_date`.

        Parameters
        ----------
        records : List[PointInTimeRecord]
            The historical candidate observations.
        as_of_date : date
            The point-in-time cutoff date (decision date).
        entity_id : Optional[str]
            Filter by entity identifier if provided.
        max_lookback_days : Optional[int]
            Staleness threshold. If latest published observation is older than this, return None.

        Returns
        -------
        AsOfJoinResult
            Structured result with match and look-ahead audit metrics.
        """
        audit_trail: List[str] = []
        candidates = records
        if entity_id:
            candidates = [r for r in candidates if r.entity_id == entity_id]

        discarded_future: int = 0
        valid_candidates: List[PointInTimeRecord] = []

        for rec in candidates:
            if rec.publication_date > as_of_date:
                discarded_future += 1
                audit_trail.append(
                    f"DISCARDED future filing: period_end={rec.period_end_date}, "
                    f"published={rec.publication_date} > as_of={as_of_date}"
                )
            else:
                valid_candidates.append(rec)

        if not valid_candidates:
            audit_trail.append(f"No valid observations published on or before {as_of_date}.")
            return AsOfJoinResult(
                as_of_date=as_of_date,
                matched_record=None,
                lag_days=None,
                total_candidates_evaluated=len(candidates),
                discarded_future_records=discarded_future,
                is_point_in_time_compliant=True,
                audit_trail=audit_trail,
            )

        # Sort by publication date descending, then period_end descending
        valid_candidates.sort(
            key=lambda r: (r.publication_date, r.period_end_date),
            reverse=True,
        )
        latest = valid_candidates[0]
        lag = (as_of_date - latest.publication_date).days

        if max_lookback_days is not None and lag > max_lookback_days:
            audit_trail.append(
                f"STALE: Latest published record ({latest.publication_date}) is {lag} days old, "
                f"exceeding max_lookback_days ({max_lookback_days})."
            )
            return AsOfJoinResult(
                as_of_date=as_of_date,
                matched_record=None,
                lag_days=lag,
                total_candidates_evaluated=len(candidates),
                discarded_future_records=discarded_future,
                is_point_in_time_compliant=True,
                audit_trail=audit_trail,
            )

        audit_trail.append(
            f"MATCHED: Period ending {latest.period_end_date}, published {latest.publication_date} "
            f"({lag} days prior to decision date {as_of_date})."
        )

        return AsOfJoinResult(
            as_of_date=as_of_date,
            matched_record=latest,
            lag_days=lag,
            total_candidates_evaluated=len(candidates),
            discarded_future_records=discarded_future,
            is_point_in_time_compliant=True,
            audit_trail=audit_trail,
        )

    @staticmethod
    def join_as_of_dataframe(
        left_df: pd.DataFrame,
        right_df: pd.DataFrame,
        on_entity: str,
        left_time_col: str,
        right_time_col: str,
    ) -> pd.DataFrame:
        """Perform an exact pandas as-of merge between time series, strictly backward-looking.

        Guarantees that `right_time_col <= left_time_col` for all merged rows.
        """
        left_sorted = left_df.sort_values(left_time_col).copy()
        right_sorted = right_df.sort_values(right_time_col).copy()

        # Ensure datetime types
        left_sorted[left_time_col] = pd.to_datetime(left_sorted[left_time_col])
        right_sorted[right_time_col] = pd.to_datetime(right_sorted[right_time_col])

        merged = pd.merge_asof(
            left_sorted,
            right_sorted,
            left_on=left_time_col,
            right_on=right_time_col,
            by=on_entity,
            direction="backward",
        )

        # Enforce look-ahead bias validation
        violators = merged[merged[right_time_col] > merged[left_time_col]]
        if not violators.empty:
            raise TargetLeakageError(
                f"AsOf Join violation detected! {len(violators)} rows contain "
                f"look-ahead data ({right_time_col} > {left_time_col})."
            )

        return merged

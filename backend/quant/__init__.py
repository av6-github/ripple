"""RIPPLE Quantitative Risk & Investment-R&D Module.

Provides institutional quant finance tools:
- Point-in-Time (PIT) As-Of Joins & Look-Ahead Bias Prevention
- Dual-Source Data Reconciliation with Tolerance-Based Checks
- Outlier Winsorisation, Cross-Sectional Ranking, Rolling/Expanding Volatility
- Feature Neutralisation (sector & size orthogonalization)
- Automated Data Quality & Balance Sheet Identity Gates
- Signal Backtesting (Information Coefficient, Rank IC, Information Ratio, AUC gain)
- Immutable Cryptographic Snapshot Lineage & Provenance
"""

from backend.quant.pit_join import AsOfJoinEngine, PointInTimeRecord
from backend.quant.reconciliation import (
    DataReconciliationService,
    ReconciliationItem,
    ReconciliationResult,
    ReconciliationStatus,
)
from backend.quant.signals import (
    compute_rolling_expanding_metrics,
    cross_sectional_percentile_rank,
    neutralize_features,
    winsorize_dataset,
    winsorize_series,
)
from backend.quant.data_quality import (
    DataQualityGate,
    DataQualityReport,
    QualityCheckResult,
)
from backend.quant.backtesting import (
    SignalBacktestResult,
    SignalEvaluator,
)
from backend.quant.provenance import (
    ProvenanceTracker,
    SnapshotProvenance,
)

__all__ = [
    "AsOfJoinEngine",
    "PointInTimeRecord",
    "DataReconciliationService",
    "ReconciliationItem",
    "ReconciliationResult",
    "ReconciliationStatus",
    "winsorize_series",
    "winsorize_dataset",
    "cross_sectional_percentile_rank",
    "compute_rolling_expanding_metrics",
    "neutralize_features",
    "DataQualityGate",
    "DataQualityReport",
    "QualityCheckResult",
    "SignalEvaluator",
    "SignalBacktestResult",
    "ProvenanceTracker",
    "SnapshotProvenance",
]

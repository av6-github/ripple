"""Authoritative Alternative Data feature calculations for RIPPLE.

Implements SRS FR-04:
- Transaction Dynamics (Frequency, Volume, Size Variability)
- Payment Behavior (Timeliness, Delay Trend, Consistency)
- Network Concentration (Customer HHI, Supplier HHI, Relationship Stability)
"""

import math
import statistics
from typing import Dict, List, Optional, Tuple
from backend.features.domain import AlternativeDataInput, CounterpartyRelationship, InvoiceRecord, TransactionRecord


def compute_transaction_features(
    transactions: List[TransactionRecord],
) -> Dict[str, Optional[float]]:
    """Compute transaction activity, volume, and variability metrics."""
    if not transactions:
        return {
            "transaction_frequency": None,
            "transaction_volume": None,
            "transaction_size_variability": None,
        }

    # Group by month
    months = set(t.transaction_date.strftime("%Y-%m") for t in transactions)
    num_months = max(1, len(months))

    # Frequency: average transactions per active month
    total_tx = len(transactions)
    freq = round(total_tx / num_months, 2)

    # Volume: average credit/inflow volume per active month
    credits = [t.amount for t in transactions if t.direction == "credit" and t.amount > 0]
    monthly_vol = round(sum(credits) / num_months, 2) if credits else 0.0

    # Size variability: coefficient of variation (std / mean)
    all_amounts = [t.amount for t in transactions]
    if len(all_amounts) >= 2:
        mean_amt = statistics.mean(all_amounts)
        if mean_amt > 1e-9:
            std_amt = statistics.stdev(all_amounts)
            var = round(std_amt / mean_amt, 4)
        else:
            var = 0.0
    else:
        var = 0.0

    return {
        "transaction_frequency": freq,
        "transaction_volume": monthly_vol,
        "transaction_size_variability": var,
    }


def compute_payment_features(
    invoices: List[InvoiceRecord],
) -> Dict[str, Optional[float]]:
    """Compute payment behavior, timeliness, delay trend, and consistency."""
    if not invoices:
        return {
            "payment_timeliness": None,
            "payment_delay_trend": None,
            "payment_consistency": None,
        }

    delays: List[float] = []
    dated_delays: List[Tuple[float, float]] = []  # (ordinal_date, delay_days)
    on_time_count = 0

    for inv in invoices:
        if inv.payment_date is not None:
            delay = (inv.payment_date - inv.due_date).days
            delays.append(float(delay))
            dated_delays.append((inv.payment_date.toordinal(), float(delay)))
            if delay <= 0:
                on_time_count += 1
        elif inv.status == "paid":
            # Paid with no recorded delay assumed on time
            delays.append(0.0)
            on_time_count += 1

    if not delays:
        return {
            "payment_timeliness": None,
            "payment_delay_trend": None,
            "payment_consistency": None,
        }

    timeliness = round(on_time_count / len(delays), 4)

    # Consistency: standard deviation of delays
    consistency = round(statistics.stdev(delays), 2) if len(delays) >= 2 else 0.0

    # Trend: slope of delays over time (positive = worsening delays)
    if len(dated_delays) >= 3:
        # Simple linear regression slope (days past due change per 30 days)
        x_vals = [pt[0] for pt in dated_delays]
        y_vals = [pt[1] for pt in dated_delays]
        x_mean = statistics.mean(x_vals)
        y_mean = statistics.mean(y_vals)
        denom = sum((x - x_mean) ** 2 for x in x_vals)
        if denom > 1e-9:
            slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, y_vals)) / denom
            # Normalize slope to days per month (30 days)
            trend = round(slope * 30.0, 4)
        else:
            trend = 0.0
    elif len(delays) >= 2:
        # Delta between second half and first half
        mid = len(delays) // 2
        trend = round(statistics.mean(delays[mid:]) - statistics.mean(delays[:mid]), 2)
    else:
        trend = 0.0

    return {
        "payment_timeliness": timeliness,
        "payment_delay_trend": trend,
        "payment_consistency": consistency,
    }


def compute_concentration_features(
    counterparties: List[CounterpartyRelationship],
) -> Dict[str, Optional[float]]:
    """Compute Herfindahl-Hirschman Index (HHI) for customers and suppliers, and stability."""
    customers = [c for c in counterparties if c.relationship_type.lower() == "customer" and c.annual_volume > 0]
    suppliers = [c for c in counterparties if c.relationship_type.lower() == "supplier" and c.annual_volume > 0]

    # Customer Concentration (HHI: sum(share^2) between 0 and 1)
    if customers:
        tot_cust_vol = sum(c.annual_volume for c in customers)
        if tot_cust_vol > 1e-9:
            cust_hhi = sum((c.annual_volume / tot_cust_vol) ** 2 for c in customers)
            cust_concentration = round(min(1.0, max(0.0, cust_hhi)), 4)
        else:
            cust_concentration = 1.0
    else:
        cust_concentration = None

    # Supplier Concentration (HHI)
    if suppliers:
        tot_supp_vol = sum(s.annual_volume for s in suppliers)
        if tot_supp_vol > 1e-9:
            supp_hhi = sum((s.annual_volume / tot_supp_vol) ** 2 for s in suppliers)
            supp_concentration = round(min(1.0, max(0.0, supp_hhi)), 4)
        else:
            supp_concentration = 1.0
    else:
        supp_concentration = None

    # Relationship Stability: average tenure in months across all counterparties
    if counterparties:
        tenures = [c.tenure_months for c in counterparties if c.tenure_months is not None]
        stability = round(statistics.mean(tenures), 1) if tenures else 0.0
    else:
        stability = None

    return {
        "customer_concentration": cust_concentration,
        "supplier_concentration": supp_concentration,
        "relationship_stability": stability,
    }


def compute_alternative_features(
    alt_data: Optional[AlternativeDataInput],
) -> Tuple[Dict[str, Optional[float]], Dict[str, bool]]:
    """Compute all alternative data features and indicator flags."""
    features: Dict[str, Optional[float]] = {}
    flags: Dict[str, bool] = {
        "alt_data_missing_flag": False,
        "invoices_missing_flag": False,
        "counterparties_missing_flag": False,
    }

    if alt_data is None:
        flags["alt_data_missing_flag"] = True
        flags["invoices_missing_flag"] = True
        flags["counterparties_missing_flag"] = True
        features.update({
            "transaction_frequency": None,
            "transaction_volume": None,
            "transaction_size_variability": None,
            "payment_timeliness": None,
            "payment_delay_trend": None,
            "payment_consistency": None,
            "customer_concentration": None,
            "supplier_concentration": None,
            "relationship_stability": None,
        })
        return features, flags

    tx_feats = compute_transaction_features(alt_data.transactions)
    if tx_feats["transaction_frequency"] is None:
        flags["alt_data_missing_flag"] = True

    inv_feats = compute_payment_features(alt_data.invoices)
    if inv_feats["payment_timeliness"] is None:
        flags["invoices_missing_flag"] = True

    conc_feats = compute_concentration_features(alt_data.counterparties)
    if conc_feats["customer_concentration"] is None and conc_feats["supplier_concentration"] is None:
        flags["counterparties_missing_flag"] = True

    features.update(tx_feats)
    features.update(inv_feats)
    features.update(conc_feats)

    return features, flags

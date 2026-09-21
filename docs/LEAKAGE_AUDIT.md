# RIPPLE Target Leakage Audit

This document governs the exclusion of post-prediction information and temporal target leakage prevention in the RIPPLE credit risk assessment platform, in strict adherence to **AGENTS.md Rule 4.5**:
> "Any feature that would only be known after the prediction point must be excluded. Examples include charge-off outcomes, recoveries, post-decision events, and other future information. The exclusion must be: (1) recorded in `docs/LEAKAGE_AUDIT.md`, (2) enforced in code, (3) covered by tests."

---

## 1. Prediction Point Definition

In RIPPLE, every credit risk assessment is evaluated at a discrete temporal decision point, designated $t_0$:
- **Prediction Point ($t_0$)**: The exact calendar timestamp at which an SME loan application is evaluated by a bank risk officer.
- **Available Information Window ($t \le t_0$)**: All historical accounting statements, tax filings, verified transaction logs, and commercial counterparty relationships timestamped on or prior to $t_0$.
- **Forbidden Future Horizon ($t > t_0$)**: All performance outcomes, loan lifecycle events, default realizations, recoveries, and post-decision commercial events occurring after $t_0$.

---

## 2. Excluded Post-Decision & Outcome Variables

The following variables are strictly classified as **Target Leakage** and are permanently blacklisted from entering the feature matrix or any model input:

| Variable / Pattern | Category | Rationale for Exclusion |
| :--- | :--- | :--- |
| `class`, `default_class`, `is_bankrupt` | Target Label | Ground truth binary bankruptcy / default outcome being predicted. |
| `charge_off`, `charge_off_amount`, `charge_off_date` | Post-Decision Event | Loan loss write-off occurring 120-180 days post default. |
| `recovery`, `recovery_amount`, `recovery_rate` | Post-Decision Event | Collections and asset liquidation proceeds realized after loan default. |
| `restructuring_event`, `forbearance_flag` | Post-Decision Event | Workout arrangements agreed between lender and borrower post-distress. |
| `post_decision_events`, `subsequent_delinquency` | Post-Decision Event | Credit bureau updates or repayment failures occurring after origination. |
| `statement_date > prediction_point` | Temporal Leakage | Financial reports or audits finalized after the loan application date $t_0$. |
| `future_revenue`, `future_ebitda` | Lookahead Bias | Projections or restatements prepared with hindsight. |
| `actual_loss`, `loss_given_default` (LGD actual) | Target Label | Empirical credit loss observed only at maturity or resolution. |

---

## 3. Enforcement Mechanisms in Code

Target leakage prevention is enforced across three defensive layers:

1. **Ingestion Layer Validation**:
   - `ValidationEngine` checks that no financial statement date is in the future relative to the ingestion timestamp (`VAL-003`).
2. **Feature Engine LeakageGuard**:
   - The central `FeatureEngine` integrates a runtime `LeakageGuard` before any feature calculation.
   - Any input dictionary, record, or DataFrame containing a blacklisted column or substring match (`class`, `charge_off`, `recovery`, `default_status`, etc.) is immediately rejected with a `TargetLeakageError`.
   - Feature generation fails closed: execution halts and no feature vector is generated.
3. **Model Training Pipeline Split Guard**:
   - In Phase 4, the tabular training dataset separates feature matrices $X$ from label vectors $y$ before preprocessing, guaranteeing that label columns are never present in the transformer pipeline.

---

## 4. Test Verification Matrix

| Test ID | Objective | Mechanism | Status |
| :--- | :--- | :--- | :--- |
| `LEAK-001` | Post-prediction variable rejection | Inject forbidden keys (`charge_off_amount`, `recovery_rate`, `default_class`) into `FeatureEngine.transform()`. Verify `TargetLeakageError` is raised. | Tested in `tests/test_feature_engine.py` |
| `LEAK-002` | Future date statement rejection | Validate financial statement dated after current date or decision point $t_0$. | Tested in `VAL-003` (`tests/test_ingestion_pipeline.py`) |
| `LEAK-003` | Feature ordering & column immutability | Validate that the feature vector schema strictly matches `docs/FEATURE_DICTIONARY.md` without rogue additions. | Tested in `tests/test_feature_engine.py` |

---

## 5. Audit Log

- **2026-09-22**: Initial leakage audit performed. Blacklist established. Enforcement implemented in `backend/features/feature_engine.py` via `LeakageGuard`. Test suite verified under `tests/test_feature_engine.py`.

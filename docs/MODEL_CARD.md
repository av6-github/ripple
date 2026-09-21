# RIPPLE Tabular Model Card: v1.0.0

## 1. Model Overview

- **Model Identifier**: `ripple-tabular-v1.0.0`
- **Model Architecture**: XGBoost Classifier with 5-fold cross-validated Isotonic Probability Calibration
- **Task**: 1-Year Forward Horizon Probability of Default (PD) Estimation
- **Created**: 2026-09-21T19:32:14.173302+00:00
- **Training Seed**: 42
- **Frameworks**: `xgboost`, `scikit-learn`, `numpy`, `scipy`

---

## 2. Dataset & Training Regime

- **Dataset**: Polish Companies Bankruptcy Dataset (5th year observation / 1-year forward default horizon)
- **Source File**: `5year.arff`
- **Dataset SHA-256**: `cb3f6f250ac46bd8d18e9a222f489fe8ee3e396fcec18959f5a0ef8e8169b2fc`
- **Train Samples**: 4728
- **Test Samples**: 1182 (20% Stratified Holdout Split)
- **Empirical Default Rate**: 6.94%
- **Input Features**: 64 Polish bankruptcy financial ratios + 3 missingness indicator features ($N = 67$)
- **Preprocessing**: Median imputation on training split, robust percentile winsorization (1st/99th percentiles)

---

## 3. Empirical Evaluation & Ablation Study

Evaluated on the unseen 20% stratified holdout test split ($N = 1182$):

| Model Candidate | ROC-AUC | PR-AUC | KS Statistic | Brier Score | ECE | F1 Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Logistic Regression (L2)** | 0.9049 | 0.6284 | 0.7209 | 0.107009 | 0.181386 | 0.4637 |
| **Random Forest (100 trees)** | 0.9323 | 0.5385 | 0.7248 | 0.054820 | 0.086969 | 0.5238 |
| **XGBoost (Uncalibrated)** | 0.9478 | 0.7670 | 0.7755 | 0.046348 | 0.075260 | 0.6344 |
| **XGBoost (Calibrated - Production)** | **0.9507** | **0.7709** | **0.7752** | **0.029327** | **0.012362** | **0.6950** |

---

## 4. Key Findings

1. **Discrimination Superiority**: Calibrated XGBoost significantly outperforms linear Logistic Regression on ROC-AUC and PR-AUC, capturing non-linear interactions across working capital, solvency leverage, and profitability ratios.
2. **Reliability & Probability Calibration**: Probability calibration dramatically reduces the Brier score and Expected Calibration Error (ECE), converting raw tree ranking scores into true probabilities suitable for regulatory credit provisioning.
3. **Imbalance Robustness**: Setting `scale_pos_weight` and calibrating with isotonic regression preserves high recall on bankrupt instances without inflating false alarms.

---

## 5. Intended Use & Limitations

- **Intended Use**: Explainable decision support for bank credit risk officers assessing SME loan applications.
- **Decision Authority**: In strict accordance with AGENTS.md Rule 4.6, this model does NOT automatically approve or reject loans. Final credit authority resides with human loan officers.
- **Out of Scope**: High-frequency consumer credit, automated consumer lending, large corporate syndicated facilities.

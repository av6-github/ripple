# RIPPLE Feature Dictionary

This document governs all features entering the RIPPLE tabular and risk assessment models, in strict compliance with **AGENTS.md Rule 15** (*Feature Dictionary Rule*):
> "Every model feature must exist in `docs/FEATURE_DICTIONARY.md`. A feature without a dictionary entry must not enter the model."

---

## 1. Governance & Specification Standards

For each feature, the dictionary defines:
- **Key**: Machine identifier used in feature arrays and code.
- **Display Label**: Human-readable label for dashboards, explainability, and reports.
- **Formula**: Mathematical calculation.
- **Inputs Required**: Underlying line items or variables.
- **Unit**: Percentage (%), Ratio, Days, Currency (PLN), Count, or Index (0 to 1).
- **Source Category**: Liquidity, Leverage, Profitability, Coverage, Operating Efficiency, Cash Flow, or Alternative Data.
- **Economic Rationale**: Financial reasoning connecting the feature to creditworthiness.
- **Expected Sign**: Expected direction of relationship with Probability of Default (PD).
  - `+` (Positive): Higher values increase PD (higher risk).
  - `-` (Negative): Higher values decrease PD (lower risk).
- **Null & Edge-Case Policy**: Handling for zero denominators, negative equity, and missing values.

---

## 2. Core Financial Features (SRS FR-04 & Polish Bankruptcy Alignment)

### 2.1 Liquidity

#### `current_ratio`
- **Display Label**: Current Ratio
- **Formula**: `current_assets / short_term_liabilities` (Corresponds to Polish attr $X_4$)
- **Inputs Required**: `current_assets`, `short_term_liabilities`
- **Unit**: Ratio
- **Source Category**: Liquidity
- **Economic Rationale**: Measures the firm's ability to cover short-term obligations with short-term assets. Low liquidity signals impending default.
- **Expected Sign**: `-` (Higher current ratio decreases PD)
- **Null Policy**: If `short_term_liabilities == 0`, capped at 50.0 and `zero_short_term_debt_flag` is set. If `current_assets` is missing, impute domain median and set missing indicator.

#### `quick_ratio`
- **Display Label**: Quick Ratio (Acid-Test)
- **Formula**: `(current_assets - inventory) / short_term_liabilities` (Corresponds to Polish attr $X_{46}$)
- **Inputs Required**: `current_assets`, `inventory`, `short_term_liabilities`
- **Unit**: Ratio
- **Source Category**: Liquidity
- **Economic Rationale**: Stricter test of liquidity excluding illiquid inventory. Critical for firms with slow inventory turns.
- **Expected Sign**: `-`
- **Null Policy**: If `short_term_liabilities == 0`, capped at 50.0. Missing inventory defaults to 0 (conservative assumption).

#### `cash_ratio`
- **Display Label**: Cash Ratio
- **Formula**: `cash_and_equivalents / short_term_liabilities` (Corresponds to Polish attr $X_{40}$)
- **Inputs Required**: `cash_and_equivalents`, `short_term_liabilities`
- **Unit**: Ratio
- **Source Category**: Liquidity
- **Economic Rationale**: Measures immediate cash liquidity available to pay pressing debts without relying on receivables collection or inventory liquidation.
- **Expected Sign**: `-`
- **Null Policy**: If `short_term_liabilities == 0`, capped at 50.0. If `cash` is missing, impute 0.0 with flag.

#### `working_capital_to_assets`
- **Display Label**: Working Capital to Total Assets
- **Formula**: `(current_assets - short_term_liabilities) / total_assets` (Corresponds to Polish attr $X_3$)
- **Inputs Required**: `current_assets`, `short_term_liabilities`, `total_assets`
- **Unit**: Ratio
- **Source Category**: Liquidity
- **Economic Rationale**: Relative net liquid assets scaled by firm size. Frequently negative in distressed firms.
- **Expected Sign**: `-`
- **Null Policy**: If `total_assets <= 0`, flagged as invalid balance sheet; capped in range `[-1.0, 1.0]`.

#### `working_capital_to_revenue`
- **Display Label**: Working Capital to Revenue
- **Formula**: `(current_assets - short_term_liabilities) / total_revenue`
- **Inputs Required**: `current_assets`, `short_term_liabilities`, `total_revenue`
- **Unit**: Ratio
- **Source Category**: Liquidity
- **Economic Rationale**: Working capital intensity relative to commercial throughput.
- **Expected Sign**: `-`
- **Null Policy**: If `total_revenue == 0`, set to 0.0 with zero-revenue flag.

---

### 2.2 Leverage & Solvency

#### `debt_to_equity`
- **Display Label**: Debt to Equity
- **Formula**: `total_liabilities / total_equity` (Derived from Polish $X_2 / X_{10}$)
- **Inputs Required**: `total_liabilities`, `total_equity`
- **Unit**: Ratio
- **Source Category**: Leverage
- **Economic Rationale**: Measures financial leverage and the cushion provided by shareholder equity against insolvency.
- **Expected Sign**: `+` (Higher debt relative to equity increases PD)
- **Null Policy**: If `total_equity <= 0` (negative equity / balance sheet insolvency), set `negative_equity_flag = True`, cap ratio at +50.0 distress ceiling (preventing sign reversal artifact where negative equity produces negative ratio that looks low-risk).

#### `debt_to_assets`
- **Display Label**: Debt to Total Assets (Debt Ratio)
- **Formula**: `total_liabilities / total_assets` (Corresponds to Polish attr $X_2$)
- **Inputs Required**: `total_liabilities`, `total_assets`
- **Unit**: Ratio
- **Source Category**: Leverage
- **Economic Rationale**: Proportion of total assets financed through debt obligations. Values $> 1.0$ indicate balance sheet insolvency.
- **Expected Sign**: `+`
- **Null Policy**: Clamped to $[0.0, 10.0]$.

#### `net_debt_to_ebitda`
- **Display Label**: Net Debt to EBITDA
- **Formula**: `(total_liabilities - cash_and_equivalents) / ebitda`
- **Inputs Required**: `total_liabilities`, `cash_and_equivalents`, `ebitda`
- **Unit**: Ratio (Years)
- **Source Category**: Leverage
- **Economic Rationale**: Number of years required to repay net debt using operating cash generation capacity before interest, taxes, and non-cash charges.
- **Expected Sign**: `+`
- **Null Policy**: If `ebitda <= 0`, set `negative_ebitda_flag = True` and clamp to +20.0.

#### `equity_ratio`
- **Display Label**: Equity to Total Assets
- **Formula**: `total_equity / total_assets` (Corresponds to Polish attr $X_{10}$)
- **Inputs Required**: `total_equity`, `total_assets`
- **Unit**: Ratio
- **Source Category**: Leverage
- **Economic Rationale**: Solvency cushion. Negative values represent complete shareholder capital erosion.
- **Expected Sign**: `-`
- **Null Policy**: Range $[-2.0, 1.0]$.

---

### 2.3 Profitability

#### `gross_margin`
- **Display Label**: Gross Profit Margin
- **Formula**: `gross_profit / total_revenue` (Corresponds to Polish attr $X_{19}$)
- **Inputs Required**: `gross_profit`, `total_revenue`
- **Unit**: Percentage / Ratio
- **Source Category**: Profitability
- **Economic Rationale**: Markup efficiency over cost of goods sold. Provides buffer to absorb operating expenses.
- **Expected Sign**: `-`
- **Null Policy**: If `total_revenue <= 0`, set to 0.0 with flag. Clamped to $[-1.0, 1.0]$.

#### `operating_margin`
- **Display Label**: Operating Margin (EBIT Margin)
- **Formula**: `operating_profit_ebit / total_revenue` (Corresponds to Polish attr $X_{39}$ / $X_{42}$)
- **Inputs Required**: `operating_profit_ebit`, `total_revenue`
- **Unit**: Percentage / Ratio
- **Source Category**: Profitability
- **Economic Rationale**: Core profitability of ongoing operations before financing costs and taxes.
- **Expected Sign**: `-`
- **Null Policy**: If `total_revenue <= 0`, set to 0.0. Clamped to $[-2.0, 1.0]$.

#### `net_margin`
- **Display Label**: Net Profit Margin
- **Formula**: `net_profit / total_revenue` (Corresponds to Polish attr $X_{23}$)
- **Inputs Required**: `net_profit`, `total_revenue`
- **Unit**: Percentage / Ratio
- **Source Category**: Profitability
- **Economic Rationale**: Bottom-line profitability after all expenses, interest, and taxes.
- **Expected Sign**: `-`
- **Null Policy**: If `total_revenue <= 0`, set to 0.0. Clamped to $[-2.0, 1.0]$.

#### `roa`
- **Display Label**: Return on Assets (ROA)
- **Formula**: `net_profit / total_assets` (Corresponds to Polish attr $X_1$)
- **Inputs Required**: `net_profit`, `total_assets`
- **Unit**: Percentage / Ratio
- **Source Category**: Profitability
- **Economic Rationale**: Operational efficiency in deploying asset base to generate net earnings.
- **Expected Sign**: `-`
- **Null Policy**: If `total_assets <= 0`, flagged. Clamped to $[-2.0, 1.0]$.

#### `roe`
- **Display Label**: Return on Equity (ROE)
- **Formula**: `net_profit / total_equity` (Corresponds to Polish attr $X_{13}$ proxy)
- **Inputs Required**: `net_profit`, `total_equity`
- **Unit**: Percentage / Ratio
- **Source Category**: Profitability
- **Economic Rationale**: Return generated on shareholders' capital base.
- **Expected Sign**: `-`
- **Null Policy**: If `total_equity <= 0`, set `negative_equity_flag = True`, clamp to $-1.0$ (avoiding false positive when both net profit and equity are negative).

---

### 2.4 Coverage

#### `interest_coverage`
- **Display Label**: Interest Coverage Ratio (TIE)
- **Formula**: `operating_profit_ebit / interest_expense` (Corresponds to Polish attr $X_{27}$)
- **Inputs Required**: `operating_profit_ebit`, `interest_expense`
- **Unit**: Ratio
- **Source Category**: Coverage
- **Economic Rationale**: Number of times EBIT covers debt service interest charges. Low or negative values indicate debt servicing distress.
- **Expected Sign**: `-` (Higher coverage lowers PD)
- **Null Policy**: If `interest_expense == 0`, firm carries no interest-bearing debt; capped at +50.0 and `zero_interest_expense_flag = True`.

#### `dscr`
- **Display Label**: Debt Service Coverage Ratio
- **Formula**: `operating_cash_flow / (short_term_liabilities + interest_expense)`
- **Inputs Required**: `operating_cash_flow`, `short_term_liabilities`, `interest_expense`
- **Unit**: Ratio
- **Source Category**: Coverage
- **Economic Rationale**: Cash flow available to meet principal and interest commitments. Values $< 1.0$ mean cash generation cannot cover upcoming debt service.
- **Expected Sign**: `-`
- **Null Policy**: If debt service == 0, capped at 50.0.

---

### 2.5 Cash Flow Dynamics

#### `ocf_to_revenue`
- **Display Label**: Operating Cash Flow to Revenue
- **Formula**: `operating_cash_flow / total_revenue`
- **Inputs Required**: `operating_cash_flow`, `total_revenue`
- **Unit**: Ratio
- **Source Category**: Cash Flow
- **Economic Rationale**: Cash conversion rate of top-line sales. Detects aggressive revenue recognition unbacked by cash collections.
- **Expected Sign**: `-`
- **Null Policy**: If `total_revenue <= 0`, set to 0.0.

#### `ocf_to_total_debt`
- **Display Label**: Operating Cash Flow to Total Debt
- **Formula**: `operating_cash_flow / total_liabilities`
- **Inputs Required**: `operating_cash_flow`, `total_liabilities`
- **Unit**: Ratio
- **Source Category**: Cash Flow
- **Economic Rationale**: Capacity to amortize outstanding liabilities out of operating cash flow.
- **Expected Sign**: `-`
- **Null Policy**: If `total_liabilities == 0`, capped at 50.0.

#### `accrual_quality`
- **Display Label**: Accrual Quality (Earnings Quality)
- **Formula**: `(net_profit - operating_cash_flow) / total_assets`
- **Inputs Required**: `net_profit`, `operating_cash_flow`, `total_assets`
- **Unit**: Ratio
- **Source Category**: Cash Flow
- **Economic Rationale**: High positive accruals (accounting earnings exceeding cash flow) often signal lower earnings quality or distress.
- **Expected Sign**: `+` (High accruals increase default risk)
- **Null Policy**: Clamped to $[-1.0, 1.0]$.

#### `cash_flow_volatility`
- **Display Label**: Cash Flow Volatility
- **Formula**: `std(operating_cash_flow_t) / mean(|operating_cash_flow_t|)` across available periods $t \in [1..T]$
- **Inputs Required**: Historical `operating_cash_flow` series
- **Unit**: Ratio (Coefficient of Variation)
- **Source Category**: Cash Flow
- **Economic Rationale**: Erratic cash generation impairs predictable debt service.
- **Expected Sign**: `+`
- **Null Policy**: Requires $\ge 2$ periods. If single period, return `None` and set `insufficient_periods_flag = True`.

---

### 2.6 Operating Efficiency & Working Capital Cycle

#### `dso`
- **Display Label**: Days Sales Outstanding (Receivables Collection Period)
- **Formula**: `(accounts_receivable * 365) / total_revenue` (Corresponds to Polish attr $X_{44}$)
- **Inputs Required**: `accounts_receivable`, `total_revenue`
- **Unit**: Days
- **Source Category**: Operating Efficiency
- **Economic Rationale**: Average days to collect trade receivables. Lengthening DSO signals customer distress or commercial disputes.
- **Expected Sign**: `+` (Lengthening DSO increases PD)
- **Null Policy**: If `total_revenue <= 0`, capped at 365 days. Clamped to $[0, 730]$.

#### `dpo`
- **Display Label**: Days Payables Outstanding
- **Formula**: `(accounts_payable * 365) / cost_of_goods_sold` (Corresponds to Polish attr $X_{52}$)
- **Inputs Required**: `accounts_payable`, `cost_of_goods_sold` (or `total_revenue` proxy)
- **Unit**: Days
- **Source Category**: Operating Efficiency
- **Economic Rationale**: Average days taken to pay trade suppliers. Extreme DPO often indicates liquidity strain where suppliers are involuntary lenders.
- **Expected Sign**: `+`
- **Null Policy**: Clamped to $[0, 730]$.

#### `dio`
- **Display Label**: Days Inventory Outstanding
- **Formula**: `(inventory * 365) / cost_of_goods_sold` (Corresponds to Polish attr $X_{47}$)
- **Inputs Required**: `inventory`, `cost_of_goods_sold`
- **Unit**: Days
- **Source Category**: Operating Efficiency
- **Economic Rationale**: Days inventory remains held before sale. High DIO ties up working capital in unsold or obsolete stock.
- **Expected Sign**: `+`
- **Null Policy**: Clamped to $[0, 730]$.

#### `cash_conversion_cycle`
- **Display Label**: Cash Conversion Cycle (CCC)
- **Formula**: `dso + dio - dpo`
- **Inputs Required**: `dso`, `dio`, `dpo`
- **Unit**: Days
- **Source Category**: Operating Efficiency
- **Economic Rationale**: Days elapsed from cash outflow for inputs to cash recovery from customer sales.
- **Expected Sign**: `+`
- **Null Policy**: If any component missing, CCC set to `None` with indicator.

#### `asset_turnover`
- **Display Label**: Total Asset Turnover
- **Formula**: `total_revenue / total_assets` (Corresponds to Polish attr $X_9$ / $X_{36}$)
- **Inputs Required**: `total_revenue`, `total_assets`
- **Unit**: Ratio
- **Source Category**: Operating Efficiency
- **Economic Rationale**: Revenue generated per unit of asset capital.
- **Expected Sign**: `-`
- **Null Policy**: Clamped to $[0.0, 20.0]$.

---

### 2.7 Trend & Growth Metrics

#### `yoy_sales_growth`
- **Display Label**: Year-over-Year Sales Growth
- **Formula**: `(total_revenue_t - total_revenue_{t-1}) / |total_revenue_{t-1}|` (Corresponds to Polish attr $X_{21}$)
- **Inputs Required**: Multi-period revenue statements
- **Unit**: Percentage / Ratio
- **Source Category**: Growth & Trend
- **Economic Rationale**: Contraction in top-line sales threatens fixed cost coverage and viability.
- **Expected Sign**: `-` (Positive growth lowers PD)
- **Null Policy**: Requires $\ge 2$ periods. If single period, return `None` and set `trend_missing_flag = True`. Clamped to $[-1.0, 5.0]$.

#### `revenue_volatility`
- **Display Label**: Revenue Volatility
- **Formula**: `std(revenue_t) / mean(revenue_t)` across available periods
- **Inputs Required**: Multi-period revenue
- **Unit**: Ratio
- **Source Category**: Growth & Trend
- **Economic Rationale**: Unstable revenues hinder debt commitments.
- **Expected Sign**: `+`
- **Null Policy**: Requires $\ge 2$ periods.

#### `margin_trend`
- **Display Label**: Operating Margin Trend
- **Formula**: `operating_margin_t - operating_margin_{t-1}`
- **Inputs Required**: Multi-period operating margin
- **Unit**: Percentage / Delta
- **Source Category**: Growth & Trend
- **Economic Rationale**: Deteriorating margins precede operating losses and cash exhaustion.
- **Expected Sign**: `-` (Improving margin lowers PD)
- **Null Policy**: Requires $\ge 2$ periods.

---

## 3. Alternative Data Features (SRS FR-04 & Bank Alternative Data)

### 3.1 Transaction Dynamics

#### `transaction_frequency`
- **Display Label**: Monthly Transaction Count
- **Formula**: Average monthly bank statement transaction count across trailing 6-12 months.
- **Inputs Required**: Bank transaction ledger records
- **Unit**: Count
- **Source Category**: Alternative Data
- **Economic Rationale**: Active commercial activity; abrupt collapse in transaction velocity reflects operational stagnation.
- **Expected Sign**: `-`
- **Null Policy**: If no banking transactions available, returns `None` with `alt_data_missing_flag = True`.

#### `transaction_volume`
- **Display Label**: Monthly Transaction Inflow Volume
- **Formula**: Average monthly total credit/inflow volume in currency (PLN).
- **Inputs Required**: Bank transaction ledger records
- **Unit**: Currency (PLN)
- **Source Category**: Alternative Data
- **Economic Rationale**: Real-time cash throughput verifying reported revenues.
- **Expected Sign**: `-`
- **Null Policy**: None if unavailable.

#### `transaction_size_variability`
- **Display Label**: Transaction Size Variability
- **Formula**: Coefficient of variation (`std(amount) / mean(amount)`) of transaction amounts.
- **Inputs Required**: Bank transaction records
- **Unit**: Ratio
- **Source Category**: Alternative Data
- **Economic Rationale**: Extreme lumpiness in inflows increases liquidity gap vulnerability.
- **Expected Sign**: `+`
- **Null Policy**: None if transaction count $< 5$.

---

### 3.2 Payment Behavior

#### `payment_timeliness`
- **Display Label**: On-Time Payment Rate
- **Formula**: `(count of invoices paid <= due_date) / (total closed invoices)`
- **Inputs Required**: Trade payable invoice records
- **Unit**: Percentage (0.0 to 1.0)
- **Source Category**: Alternative Data
- **Economic Rationale**: Direct measure of debtor discipline. Low on-time payment is the strongest leading indicator of default.
- **Expected Sign**: `-` (High timeliness lowers PD)
- **Null Policy**: Returns 1.0 if zero payables exist, or `None` if no invoice data provided.

#### `payment_delay_trend`
- **Display Label**: Payment Delay Trend
- **Formula**: Linear regression slope (or $\Delta$) of Average Days Past Due (DPD) over trailing 3 quarters.
- **Inputs Required**: Trailing invoice payment dates
- **Unit**: Days / Month
- **Source Category**: Alternative Data
- **Economic Rationale**: Positive trend indicates lengthening payment delays and creeping liquidity stress.
- **Expected Sign**: `+`
- **Null Policy**: None if $< 2$ measurement windows.

#### `payment_consistency`
- **Display Label**: Payment Delay Standard Deviation
- **Formula**: Standard deviation of days past due across all settled invoices.
- **Inputs Required**: Invoice payment dates
- **Unit**: Days
- **Source Category**: Alternative Data
- **Economic Rationale**: Inconsistent settlement schedules reveal disorganization and cash rationing.
- **Expected Sign**: `+`
- **Null Policy**: 0.0 if all payments made on exact same schedule.

---

### 3.3 Counterparty & Commercial Network Concentration

#### `customer_concentration`
- **Display Label**: Customer Concentration (HHI)
- **Formula**: Herfindahl-Hirschman Index $\sum_{i=1}^K s_i^2$, where $s_i$ is customer $i$'s revenue share ($\sum s_i = 1.0$). Normalized between 0 and 1.
- **Inputs Required**: Accounts receivable / customer invoice distribution
- **Unit**: Index ($[0.0, 1.0]$)
- **Source Category**: Alternative Data
- **Economic Rationale**: High concentration ($HHI > 0.25$) exposes the SME to severe domino default risk if a key buyer fails or delays payment.
- **Expected Sign**: `+`
- **Null Policy**: If no customer breakdown provided, imputed at market average ($0.15$) with unverified flag.

#### `supplier_concentration`
- **Display Label**: Supplier Concentration (HHI)
- **Formula**: Herfindahl-Hirschman Index $\sum_{j=1}^M w_j^2$, where $w_j$ is supplier $j$'s procurement spend share.
- **Inputs Required**: Accounts payable / supplier procurement distribution
- **Unit**: Index ($[0.0, 1.0]$)
- **Source Category**: Alternative Data
- **Economic Rationale**: Single-source supplier dependency creates supply chain vulnerability and pricing power weakness.
- **Expected Sign**: `+`
- **Null Policy**: Imputed at market average ($0.15$) if unverified.

#### `relationship_stability`
- **Display Label**: Commercial Relationship Stability
- **Formula**: Average tenure (months) across top-5 customer and supplier relationships.
- **Inputs Required**: Graph / commercial relationship counterparty tenures
- **Unit**: Months
- **Source Category**: Alternative Data
- **Economic Rationale**: Established, multi-year commercial partnerships signal reliable trading partners and resilience.
- **Expected Sign**: `-` (Longer relationships lower PD)
- **Null Policy**: Capped at 120 months.

---

## 4. Polish Bankruptcy Attribute Mapping ($X_1..X_{64}$)

All 64 attributes from the Polish dataset are preserved verbatim with lossless mapping to their CFA analytical categories as established in `docs/DATASET.md`. When training tabular models on the Polish dataset, the model can consume either:
1. The 64 normalized Polish attributes directly.
2. The derived financial and alternative ratio dictionary.
The feature engine supports bidirectional mapping where raw statement inputs populate $X_1..X_{64}$ proxies and vice versa.

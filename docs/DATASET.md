# RIPPLE — Dataset Documentation & Governance

## 1. Primary Dataset Overview

**Dataset Name:** Polish Companies Bankruptcy Data  
**Origin / Curators:** Maciej Zięba, Sebastian K. Tomczak, Jakub M. Tomczak (Wrocław University of Technology, Poland, 2016)  
**Host:** UCI Machine Learning Repository (Dataset ID: 365)  
**Primary Reference:**  
Zięba, M., Tomczak, S. K., & Tomczak, J. M. (2016). *Ensemble boosted trees with synthetic features generation in application to bankruptcy prediction*. Expert Systems with Applications, 58, 93-101.  
**Data Source:** Emerging Markets Information Service (EMIS / ISI Emerging Markets)  
**Licence:** Creative Commons Attribution 4.0 International (CC BY 4.0)

---

## 2. Temporal & Forecasting Structure

The dataset contains five distinct ARFF files corresponding to different forecasting time horizons. Bankrupt companies were evaluated over the period 2000–2012, while operating/surviving companies were evaluated from 2007 to 2013.

| File | Forecasting Horizon | Observation Period | Rows | Bankrupt (`class=1`) | Healthy (`class=0`) | Default Rate | Missing Values |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `1year.arff` | 5 years forward | 1st year of period | 7,027 | 271 | 6,756 | 3.86% | 5,835 (1.30%) |
| `2year.arff` | 4 years forward | 2nd year of period | 10,173 | 400 | 9,773 | 3.93% | 12,157 (1.87%) |
| `3year.arff` | 3 years forward | 3rd year of period | 10,503 | 495 | 10,008 | 4.71% | 9,888 (1.47%) |
| `4year.arff` | 2 years forward | 4th year of period | 9,792 | 515 | 9,277 | 5.26% | 8,776 (1.40%) |
| `5year.arff` | 1 year forward | 5th year of period | 5,910 | 410 | 5,500 | 6.94% | 4,666 (1.23%) |

> [!CAUTION]
> **No Concatenation Rule (ADR-001):**  
> The five files MUST NOT be naively concatenated. Because company identifiers were anonymized by the original authors, concatenating files would cause repeated observations of the same firms to leak across train/validation splits. Each forecasting case is evaluated independently.

---

## 3. Variable Definitions (64 Features)

The dataset contains 64 financial ratios ($X_1$ through $X_{64}$):

| Feature | Formal Definition | Analytical Category |
| :--- | :--- | :--- |
| **X1** | Net profit / total assets (ROA) | Profitability |
| **X2** | Total liabilities / total assets (Debt Ratio) | Leverage / Solvency |
| **X3** | Working capital / total assets | Liquidity |
| **X4** | Current assets / short-term liabilities (Current Ratio) | Liquidity |
| **X5** | [(Cash + securities + receivables - short-term liabilities) / (operating expenses - depreciation)] $\times$ 365 | Liquidity |
| **X6** | Retained earnings / total assets | Liquidity / Capital |
| **X7** | EBIT / total assets | Profitability |
| **X8** | Book value of equity / total liabilities | Leverage / Solvency |
| **X9** | Sales / total assets | Operating Efficiency |
| **X10** | Equity / total assets | Leverage / Solvency |
| **X11** | (Gross profit + extraordinary items + financial expenses) / total assets | Profitability |
| **X12** | Gross profit / short-term liabilities | Liquidity |
| **X13** | (Gross profit + depreciation) / sales | Profitability |
| **X14** | (Gross profit + interest) / total assets | Profitability |
| **X15** | (Total liabilities $\times$ 365) / (gross profit + depreciation) | Efficiency / Activity |
| **X16** | (Gross profit + depreciation) / total liabilities | Leverage / Solvency |
| **X17** | Total assets / total liabilities | Leverage / Solvency |
| **X18** | Gross profit / total assets | Profitability |
| **X19** | Gross profit / sales (Gross Margin) | Profitability |
| **X20** | (Inventory $\times$ 365) / sales | Efficiency / Activity |
| **X21** | Sales($n$) / sales($n-1$) | Growth |
| **X22** | Profit on operating activities / total assets | Profitability |
| **X23** | Net profit / sales (Net Margin) | Profitability |
| **X24** | Gross profit (trailing 3 years) / total assets | Profitability |
| **X25** | (Equity - share capital) / total assets | Capital Structure |
| **X26** | (Net profit + depreciation) / total liabilities | Leverage / Solvency |
| **X27** | Profit on operating activities / financial expenses (Interest Coverage) | Coverage |
| **X28** | Working capital / fixed assets | Liquidity |
| **X29** | Logarithm of total assets (Firm Scale Proxy) | Scale |
| **X30** | (Total liabilities - cash) / sales | Efficiency / Activity |
| **X31** | (Gross profit + interest) / sales | Coverage |
| **X32** | (Current liabilities $\times$ 365) / cost of products sold | Efficiency / Activity |
| **X33** | Operating expenses / short-term liabilities | Liquidity |
| **X34** | Operating expenses / total liabilities | Leverage / Solvency |
| **X35** | Profit on sales / total assets | Profitability |
| **X36** | Total sales / total assets | Operating Efficiency |
| **X37** | (Current assets - inventories) / long-term liabilities | Liquidity |
| **X38** | Constant capital / total assets | Capital Structure |
| **X39** | Profit on sales / sales (Operating Margin) | Profitability |
| **X40** | (Current assets - inventory - receivables) / short-term liabilities | Liquidity |
| **X41** | Total liabilities / ((profit on operating activities + depreciation) $\times$ (12/365)) | Coverage |
| **X42** | Profit on operating activities / sales | Profitability |
| **X43** | Rotation receivables + inventory turnover in days | Efficiency / Activity |
| **X44** | (Receivables $\times$ 365) / sales (DSO) | Efficiency / Activity |
| **X45** | Net profit / inventory | Coverage |
| **X46** | (Current assets - inventory) / short-term liabilities (Quick Ratio) | Liquidity |
| **X47** | (Inventory $\times$ 365) / cost of products sold (DIO) | Efficiency / Activity |
| **X48** | EBITDA / total assets | Profitability |
| **X49** | EBITDA / sales | Profitability |
| **X50** | Current assets / total liabilities | Leverage / Solvency |
| **X51** | Short-term liabilities / total assets | Leverage / Solvency |
| **X52** | (Short-term liabilities $\times$ 365) / cost of products sold (DPO) | Efficiency / Activity |
| **X53** | Equity / fixed assets | Liquidity |
| **X54** | Constant capital / fixed assets | Liquidity |
| **X55** | Working capital (raw monetary value in PLN) | Liquidity |
| **X56** | (Sales - cost of products sold) / sales | Coverage |
| **X57** | (Current assets - inventory - short-term liabilities) / (sales - gross profit - depreciation) | Liquidity |
| **X58** | Total costs / total sales | Cost Structure |
| **X59** | Long-term liabilities / equity | Leverage / Solvency |
| **X60** | Sales / inventory | Efficiency / Activity |
| **X61** | Sales / receivables | Efficiency / Activity |
| **X62** | (Short-term liabilities $\times$ 365) / sales | Efficiency / Activity |
| **X63** | Sales / short-term liabilities | Efficiency / Activity |
| **X64** | Sales / fixed assets | Efficiency / Activity |

---

## 4. Missingness & Quality Policy

1. **High Missingness Attributes:**
   - $X_{37}$ has ~45% missing values due to zero long-term liabilities.
   - $X_{21}$ has up to 31% missing values due to missing $n-1$ prior-year sales records.
   - $X_{27}$ has ~6.6% missing values due to zero financial/interest expenses.
2. **Policy:**
   - High missingness features are never dropped unconditionally if economically critical. Missingness is handled with indicator flags and median imputation in the feature engine.
   - Completeness is tracked per record; any assessment input with $< 60\%$ verified fields triggers `INCONCLUSIVE` (SRS FR-03/Completeness Gate).

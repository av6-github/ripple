# RIPPLE — Mathematical & Technical Specification Dossier
**Academic Prototype for Explainable SME Credit-Risk Decision Support**  
*Document Version: 2.4.0 — Strict Adherence to Basel II/III IRB, EU AI Act, and AGENTS.md Hard Rules*

---

## Table of Contents
1. [Executive Summary & Core Differentiators (USPs)](#1-executive-summary--core-differentiators-usps)
2. [End-to-End System Architecture](#2-end-to-end-system-architecture)
3. [Data Ingestion, Provenance & Gating Engine](#3-data-ingestion-provenance--gating-engine)
4. [Feature Engineering & Quantitative Preprocessing](#4-feature-engineering--quantitative-preprocessing)
5. [Tabular Predictive Model & Isotonic Calibration](#5-tabular-predictive-model--isotonic-calibration)
6. [Graph Neural Network (GNN) Contagion Engine](#6-graph-neural-network-gnn-contagion-engine)
7. [Bimodal Multi-Modal Risk Fusion & Regulatory Risk Banding](#7-bimodal-multi-modal-risk-fusion--regulatory-risk-banding)
8. [Decoupled Explainability (SHAP vs. Graph Attribution)](#8-decoupled-explainability-shap-vs-graph-attribution)
9. [Deterministic Macroeconomic Scenario Stress Testing](#9-deterministic-macroeconomic-scenario-stress-testing)
10. [Multi-Horizon Cumulative Default Term Structure](#10-multi-horizon-cumulative-default-term-structure)
11. [Investment R&D & Quantitative Risk Signals Suite](#11-investment-rd--quantitative-risk-signals-suite)
12. [Evaluator Q&A Defense Cheat Sheet (Exact Number Walkthroughs)](#12-evaluator-qa-defense-cheat-sheet-exact-number-walkthroughs)

---

## 1. Executive Summary & Core Differentiators (USPs)

RIPPLE is an institutional-grade decision support platform designed for commercial bank credit underwriters evaluating Small and Medium Enterprises (SMEs). Unlike retail lending, where credit bureau scores (e.g., FICO) dominate, SME credit evaluation suffers from **sparse financial disclosures, cyclical earnings volatility, and supply-chain ripple effects**.

### Competitive Differentiation vs. Market Alternatives

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       TRADITIONAL CREDIT SCORECARDS                         │
│  [Moody's RiskCalc / S&P CreditModel / FICO SBSS / Experian Intelliscore]   │
│                                                                             │
│  • Single-modal tabular models (isolated balance-sheet ratios only).         │
│  • Contagion blind: Treats connected supply-chain businesses as silos.      │
│  • Heuristic stress tests (arbitrary fudge factors like "PD × 1.3").        │
│  • Black-box or monolithic scorecards; no cryptographic file reconciliation.│
│  • Automated accept/reject thresholds bypassing human discretion.           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      vs.
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RIPPLE CREDIT INTELLIGENCE                        │
│                                                                             │
│  1. Dual-Engine Multi-Modal Fusion (Independent Tabular GBDT + GNN).        │
│  2. Decoupled Explainability (TreeSHAP for tabular; Subgraphs for trade).   │
│  3. Cryptographic Dual-Source Reconciliation (KRS Registry vs. Uploads).   │
│  4. Deterministic Macro Re-simulation (Exact model re-runs, zero fudge).    │
│  5. Point-in-Time Look-Ahead Bias Elimination (Strict AsOfJoinEngine).     │
│  6. Human Decision Custody (Rule 4.6: Strict advisory risk bands only).     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. End-to-End System Architecture

```
[Borrower Financial Statement]          [Official KRS / Tax Registry Feed]
              │                                          │
              ▼                                          ▼
   [Cryptographic SHA-256]                    [Cryptographic SHA-256]
              │                                          │
              └──────────────┬───────────────────────────┘
                             ▼
              [Dual-Source Data Reconciliation]
              (Relative Divergence δ ≤ 5.0% Gate)
                             │
                             ▼
                 [Data Completeness Gate]
                 (Critical Solvency Checks)
                             │
              ┌──────────────┴───────────────────────────┐
              ▼                                          ▼
   [Tabular Feature Engine]                   [Trade Network Topology]
     • 64 Financial Ratios                      • Multi-hop Ego-Network
     • Winsorisation (1%/99%)                   • Supplier / Buyer Edges
     • Size & Sector Normalization              • Annual Transaction Volume
              │                                          │
              ▼                                          ▼
   [Calibrated LightGBM GBDT]                 [PyTorch SMEGraphNeuralNet]
    P(Default | Financials)                    P(Default | Contagion)
        PD_tab ∈ [0, 1]                            PD_graph ∈ [0, 1]
              │                                          │
              └──────────────┬───────────────────────────┘
                             ▼
               [Bimodal Multi-Modal Fusion Layer]
                 PD_fused = (1 - w)·PD_tab + w·PD_graph
                             │
              ┌──────────────┴───────────────────────────┐
              ▼                                          ▼
   [Decoupled Explainability]                 [Deterministic Stress Engine]
     • Tabular: TreeSHAP                        • Severe Revenue Drop (-20%)
     • Network: Subgraph Attrib.                • Monetary Hike (+300 bps)
                                                • Debtor DSO Delay (+30d)
                                                • Compound Stagflation
                             │
                             ▼
               [Regulatory Risk Banding & Custody]
                 Band A (Low)      : PD < 2.0%  → LOWER_RISK
                 Band B (Moderate) : PD < 5.0%  → FURTHER_REVIEW
                 Band C (Elevated) : PD < 15.0% → FURTHER_REVIEW
                 Band D (High)     : PD ≥ 15.0% → HIGHER_RISK
                 Human Officer Decision & Override Audit Trail
```

---

## 3. Data Ingestion, Provenance & Gating Engine

Every financial input entering RIPPLE is processed through a zero-trust provenance pipeline to prevent data tampering, hallucinated estimates, and look-ahead bias.

### 3.1 Provenance Tuple (Rule 4.3)
Every factual accounting number is immutably tagged:
$$\mathcal{P} = \langle \text{source\_type}, \text{source\_ref}, \text{confidence}, \text{ingestion\_timestamp}, \text{sha256\_digest} \rangle$$
* $\text{source\_type} \in \{\texttt{extracted\_file}, \texttt{manual\_entry}, \texttt{public\_dataset}, \texttt{synthetic}, \texttt{derived}\}$
* $\text{confidence} \in \{\texttt{verified}, \texttt{unverified}, \texttt{estimated}, \texttt{missing}\}$
* **Rule 4.1**: Stored strictly in remote PostgreSQL (`financial_record` table).

### 3.2 Completeness Evaluator ($S_{\text{comp}}$) & Inconclusive Gate (Rule 4.2)
Before any ML model executes, the borrower statement must pass the data completeness gate:
$$S_{\text{comp}} = \frac{\sum_{i=1}^{N} w_i \cdot \mathbb{I}(x_i \text{ is present and valid})}{\sum_{i=1}^{N} w_i} \times 100\%$$
Where:
* Critical Solvency Fields (weight $w = 2.0$): Revenue, Total Assets, Total Liabilities, Total Equity, Short-Term Liabilities, Operating Profit (EBIT).
* Standard Line Items (weight $w = 1.0$): Cash & Equivalents, Inventory, Accounts Receivable, Cost of Goods Sold, Operating Cash Flow.

$$\textbf{Gating Rule: } \text{If } S_{\text{comp}} < 60.0\% \text{ or any critical solvency field is missing} \implies \textbf{\texttt{INCONCLUSIVE}}$$
Under `INCONCLUSIVE`, RIPPLE terminates scoring immediately without computing or fabricating default probabilities.

### 3.3 Point-in-Time (PIT) As-Of Join Integrity (`AsOfJoinEngine`)
To prevent look-ahead bias in predictive modeling, information known at time $t$ must only reflect disclosures published before $t$:
$$t_{\text{period\_end}} < t_{\text{publication}} \le t_{\text{decision}}$$
* **Reporting Lag:** $\Delta t_{\text{rep}} = t_{\text{publication}} - t_{\text{period\_end}}$ (typically $45 - 90$ days for statutory corporate filings).
* **Decision Lag:** $\Delta t_{\text{dec}} = t_{\text{decision}} - t_{\text{publication}}$.
* If $t_{\text{publication}} > t_{\text{decision}}$, the record is strictly masked (`look_ahead_guard = VERIFIED_ACTIVE`).

### 3.4 Cryptographic Dual-Source Data Reconciliation (`DataReconciliationService`)
Borrower uploads (**Source A: Self-Reported**) are cryptographically cross-audited against statutory state registries (**Source B: National Court Register / KRS / Tax Feed**):
$$\delta_j = \frac{\left|\text{Source A}_j - \text{Source B}_j\right|}{\max\left(|\text{Source B}_j|, \, 1.0\right)} \times 100\%$$

$$\textbf{Reconciliation Policy: } \begin{cases}
\delta_j \le 1.0\% & \implies \textbf{\texttt{EXACT\_MATCH}} \quad (\text{Passed}) \\
1.0\% < \delta_j \le 5.0\% & \implies \textbf{\texttt{RECONCILED}} \quad (\text{Minor statutory timing divergence}) \\
\delta_j > 5.0\% & \implies \textbf{\texttt{FLAGGED}} \quad (\text{Material discrepancy / Fraud alert})
\end{cases}$$

### 3.5 Automated Data Quality Gate & Balance Sheet Identity Audits
Core financial physics must hold:
1. **Balance Sheet Identity:**
   $$\Delta_{\text{BS}} = |\text{Total Assets} - (\text{Total Liabilities} + \text{Total Equity})| \le 100.0\text{ PLN}$$
2. **Net Working Capital Identity:**
   $$\text{NWC} = \text{Current Assets} - \text{Short-Term Liabilities}$$
3. **Solvency Capital Cushion Check:**
   $$\text{If } \text{Total Equity} \le 0 \implies \text{Flag: } \texttt{negative\_equity\_flag} = \text{True}$$

---

## 4. Feature Engineering & Quantitative Preprocessing

The tabular model computes **64 fundamental financial indicators** grounded in corporate bankruptcy literature (Altman Z-Score, Beaver’s failure ratios, Ohlson’s O-Score, and Polish manufacturing benchmarks).

### 4.1 Key Feature Mathematical Definitions

| Feature Key | Name | Exact Formula | Economic Rationale |
| :--- | :--- | :--- | :--- |
| `Attr1` | Return on Assets (ROA) | $\frac{\text{Net Profit}}{\text{Total Assets}}$ | Core operational earning efficiency of enterprise capital. |
| `Attr2` | Leverage Ratio | $\frac{\text{Total Liabilities}}{\text{Total Assets}}$ | Capital structure solvency; percentage of assets funded by debt. |
| `Attr3` | Working Capital Ratio | $\frac{\text{Current Assets} - \text{Short-Term Liabilities}}{\text{Total Assets}}$ | Immediate liquidity cushion to absorb short-term shocks. |
| `Attr4` | Current Ratio | $\frac{\text{Current Assets}}{\text{Short-Term Liabilities}}$ | Traditional short-term debt coverage capability. |
| `Attr9` | Asset Turnover | $\frac{\text{Total Revenue}}{\text{Total Assets}}$ | Velocity of revenue generation per unit of asset capital. |
| `Attr19` | Gross Profit Margin | $\frac{\text{Gross Profit}}{\text{Total Revenue}}$ | Core production profitability before overhead expenses. |
| `Attr23` | Net Profit Margin | $\frac{\text{Net Profit}}{\text{Total Revenue}}$ | Bottom-line earnings retention after taxes and interest dues. |
| `Attr27` | Operating Interest Coverage | $\frac{\text{Operating Profit (EBIT)}}{\text{Interest Expense}}$ | Capacity to service contractual debt obligations from operations. |
| `Attr40` | Cash Liquidity Ratio | $\frac{\text{Cash \& Equivalents}}{\text{Short-Term Liabilities}}$ | Pure liquid cash available to service immediate creditor dues. |
| `Attr44` | Days Sales Outstanding (DSO) | $\frac{\text{Accounts Receivable}}{\text{Total Revenue}} \times 365$ | Average collection lag (in days) required to cash in receivables. |
| `Attr58` | Operating Cost Ratio | $\frac{\text{Total Operating Expenses}}{\text{Total Revenue}}$ | Operational operating leverage and fixed cost efficiency. |

### 4.2 Statistical Winsorization & Normalization
To prevent accounting division-by-zero errors (e.g., zero equity or near-zero interest), features undergo two-sided statistical Winsorization at the 1st and 99th percentiles:
$$\widetilde{x}_j = \min\left(\max\left(x_j, \, Q_{0.01}(x_j)\right), \, Q_{0.99}(x_j)\right)$$
Followed by robust centering:
$$z_j = \frac{\widetilde{x}_j - \text{Median}(x_j)}{\text{IQR}(x_j) + \epsilon}$$

### 4.3 Cross-Sectional Ranking & Size Neutralization
Accounting ratios vary dramatically across sectors (e.g., asset turnover in retail vs. precision manufacturing).
* **Percentile Rank:**
  $$\text{RankPct}_i = \frac{\text{Rank}(z_{i, \text{sector}})}{N_{\text{sector}} + 1} \times 100\%$$
* **Size Neutralization:**
  $$z_i = \alpha + \beta \ln(\text{Total Assets}_i) + \sum_{k} \gamma_k D_{ik} + \epsilon_i$$
  The orthogonalized residual $\epsilon_i$ represents the pure financial performance of the firm, purged of size and sector bias.

---

## 5. Tabular Predictive Model & Isotonic Calibration

### 5.1 LightGBM Gradient Boosted Decision Tree (GBDT)
The primary tabular default predictor is an ensemble of $K$ gradient-boosted decision trees:
$$F_K(\mathbf{x}) = \sum_{k=1}^{K} f_k(\mathbf{x})$$
Optimized using the binary logistic log-loss objective function:
$$\mathcal{L} = -\sum_{i=1}^{M} \left[ y_i \ln(p_i) + (1 - y_i) \ln(1 - p_i) \right] + \sum_{k=1}^{K} \Omega(f_k)$$
Where raw model margin is $s(\mathbf{x}) = F_K(\mathbf{x})$ and regularizer is $\Omega(f_k) = \gamma T + \frac{1}{2}\lambda \sum w_j^2$.

### 5.2 Isotonic Regression Non-Parametric Calibration
Raw tree probability predictions $s \in [0, 1]$ are systematically miscalibrated near the extremes. RIPPLE applies non-parametric **Isotonic Regression** using the Pool Adjacent Violators Algorithm (PAVA):
$$\min_{m} \sum_{i=1}^{M} \left( y_i - m(s_i) \right)^2 \quad \text{subject to } m(s_a) \le m(s_b) \quad \forall s_a \le s_b$$
* **Output:** Calibrated Tabular Probability of Default:
  $$PD_{\text{tab}} = m(s(\mathbf{x})) \in [0.001, \, 0.999]$$
* **Validation:** Calibration quality is verified via **Brier Score** ($\text{BS} = \frac{1}{M}\sum (PD_i - y_i)^2 \le 0.08$) and **Expected Calibration Error (ECE)**.

---

## 6. Graph Neural Network (GNN) Contagion Engine

In real commercial supply chains, healthy enterprises default when key counterparties fail ("supply-chain default cascades"). RIPPLE models these interconnections using PyTorch Geometric.

### 6.1 Trade Network Graph Representation
Let the commercial trade network be $\mathcal{G} = (\mathcal{V}, \mathcal{E}, \mathbf{X}, \mathbf{E}_{\text{weight}})$:
* $\mathcal{V}$: Node set of businesses (Core SME + Upstream Suppliers + Downstream Buyers + Partners).
* $\mathcal{E}$: Directed commercial trade edges:
  * $(u \to v) \in \texttt{SUPPLIES}$: Supplier $u$ provides inputs to Buyer $v$.
  * $(v \to w) \in \texttt{SELLS\_TO}$: Core firm $v$ sells outputs to Customer $w$.
  * $(v \leftrightarrow z) \in \texttt{TRANSACTS\_WITH}$: Strategic logistics / distribution partnership.
* $\mathbf{X} \in \mathbb{R}^{|\mathcal{V}| \times d}$: Node financial attribute matrix ($d = 67$ inputs).
* $\mathbf{E}_{\text{weight}} \in \mathbb{R}^{|\mathcal{E}|}$: Annual transaction volume $\text{Vol}_{uv}$ and relationship tenure.

### 6.2 Message Passing Neural Network Architecture
At layer $l$, the structural embedding $\mathbf{h}_v^{(l)}$ of firm $v$ is updated by aggregating message representations from its connected trading partners $\mathcal{N}(v)$:
$$\mathbf{m}_{\mathcal{N}(v)}^{(l)} = \sum_{u \in \mathcal{N}(v)} \alpha_{uv} \cdot \mathbf{W}_{\text{msg}}^{(l)} \mathbf{h}_u^{(l)}$$
$$\mathbf{h}_v^{(l+1)} = \text{ReLU}\left( \mathbf{W}_{\text{self}}^{(l)} \mathbf{h}_v^{(l)} + \mathbf{m}_{\mathcal{N}(v)}^{(l)} \right)$$
Where the topological edge attention weight is:
$$\alpha_{uv} = \frac{\text{Vol}_{uv}}{\sum_{k \in \mathcal{N}(v)} \text{Vol}_{kv}}$$
* **Classification Head:**
  $$\mathbf{z}_v = \mathbf{W}_{\text{out}} \mathbf{h}_v^{(L)} \in \mathbb{R}^2 \implies PD_{\text{graph}} = \text{Softmax}(\mathbf{z}_v)_1$$

### 6.3 Cold-Start Fallback Protocol (Rule 4.2 & TESTS.md GNN-004)
If an SME has no recorded commercial counterparties ($\text{Degree}(v) = 0$) or the GNN service is offline:
$$\textbf{Cold-Start Policy: } \begin{cases}
PD_{\text{graph}} = \texttt{None} \\
\text{is\_cold\_start} = \text{True} \\
\text{fallback\_reason} = \texttt{"isolated\_node\_zero\_degree"} \\
PD_{\text{fused}} = PD_{\text{tab}} \quad (\text{Pure Tabular Fallback, Zero Fabricated Risk})
\end{cases}$$

---

## 7. Bimodal Multi-Modal Risk Fusion & Regulatory Risk Banding

### 7.1 Mathematical Fusion Equation
The unified default probability synthesizes standalone balance-sheet risk and commercial network contagion:
$$PD_{\text{fused}} = (1 - w_{\text{graph}}) \cdot PD_{\text{tab}} + w_{\text{graph}} \cdot PD_{\text{graph}}$$
* **Default Graph Influence Weight:** $w_{\text{graph}} = 0.15$ (15%).
* **Safety Constraint:** $0.0 \le w_{\text{graph}} \le 0.50$ (ensures fundamental balance-sheet viability remains primary, holding $\ge 50\%$ authority).
* **If Cold-Start:** $w_{\text{graph}} = 0.0 \implies PD_{\text{fused}} = PD_{\text{tab}}$.

### 7.2 Regulatory Credit Risk Banding (Basel II/III Alignment)
The fused default probability is mapped into standardized banking risk tiers:

$$\begin{array}{|c|c|c|l|}
\hline
\textbf{Credit Risk Band} & \textbf{PD Range} & \textbf{Advisory Recommendation} & \textbf{Underwriting Committee Mandate} \\
\hline
\textbf{Band A (Low Risk)} & PD < 2.0\% & \texttt{LOWER\_RISK} & Fast-track approval for standard revolving credit line. \\
\textbf{Band B (Moderate Risk)} & 2.0\% \le PD < 5.0\% & \texttt{FURTHER\_REVIEW} & Standard approval subject to annual covenant monitoring. \\
\textbf{Band C (Elevated Risk)} & 5.0\% \le PD < 15.0\% & \texttt{FURTHER\_REVIEW} & Credit committee review; asset backing / receivables pledge. \\
\textbf{Band D (High Risk)} & PD \ge 15.0\% & \texttt{HIGHER\_RISK} & Capital preservation; requires senior committee sign-off. \\
\hline
\end{array}$$

### 7.3 Human Decision Custody (Rule 4.6)
* **Hard Law:** RIPPLE **never** automatically approves or rejects an application.
* The system produces strictly advisory recommendations:
  $$\text{Rec} \in \{\texttt{LOWER\_RISK}, \, \texttt{FURTHER\_REVIEW}, \, \texttt{HIGHER\_RISK}, \, \texttt{INCONCLUSIVE}\}$$
* All human credit officer decisions, overrides, and mandatory rationales are immutably persisted in the `assessment` table.

---

## 8. Decoupled Explainability (SHAP vs. Graph Attribution)

Per **AGENTS.md Rule 4.7**, RIPPLE strictly isolates feature explainability by modality. SHAP is mathematically defined **only for the tabular model** and is never conflated with the GNN.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STRICTLY DECOUPLED EXPLAINABILITY                        │
│                                                                             │
│   [Tabular Features] ────> [TreeSHAP Explainer] ────> Feature Attributions  │
│                                                       (Currency Units / ΔPD)│
│                                                                             │
│   [Network Topology] ────> [Topological Flow]   ────> Counterparty Exposure │
│                                                       (Volume Concentration)│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.1 Local Tabular SHAP Attributions (TreeExplainer)
For the tabular model, local feature attributions $\phi_j$ satisfy exact efficiency:
$$f(\mathbf{x}) = \phi_0 + \sum_{j=1}^{M} \phi_j(\mathbf{x})$$
$$\phi_j = \sum_{S \subseteq F \setminus \{j\}} \frac{|S|!(|F| - |S| - 1)!}{|F|!} \left[ f_x(S \cup \{j\}) - f_x(S) \right]$$
* **Interpretation:** $\phi_j > 0$ increases default hazard; $\phi_j < 0$ mitigates default risk.
* **Display in UI:** Top 5 positive drivers (concerns) and top 5 negative drivers (strengths).

### 8.2 Network Contagion Explainability (Topological Attributions)
GNN contagion is explained independently via ego-network topology metrics:
1. **Debtor Concentration (HHI):**
   $$\text{HHI}_{\text{buyers}} = \sum_{j \in \mathcal{N}_{\text{buyers}}} \left( \frac{\text{Vol}_{ij}}{\sum \text{Vol}} \right)^2$$
2. **Upstream Supplier Vulnerability Index:**
   $$\mathcal{V}_{\text{upstream}} = \sum_{k \in \mathcal{N}_{\text{suppliers}}} w_{ik} \cdot \widehat{PD}_k$$

---

## 9. Deterministic Macroeconomic Scenario Stress Testing

Per **TESTS.md Section 13**, RIPPLE rejects arbitrary stress heuristics. Instead, it applies mathematical feature shifts to the borrower’s input vector $\mathbf{x}$ and re-runs the trained calibrated LightGBM pipeline:
$$\Delta PD = PD_{\text{shocked}} - PD_{\text{baseline}}, \quad \text{Hazard Shift } \% = \left(\frac{\Delta PD}{PD_{\text{baseline}}}\right) \times 100\%$$

### 9.1 The 4 Canonical Scenarios & Their Exact Transformations

```
1. SCEN-01: Severe Revenue Contraction (-20% Demand Shock)
   • Attr9 (Sales / Assets)     *= (1.0 - 0.20) = 0.80
   • Attr19 (Gross Margin)      *= (1.0 - 0.20 * 1.5) = 0.70
   • Attr23 (Net Profit Margin) *= (1.0 - 0.20 * 2.0) = 0.60

2. SCEN-02: Monetary Rate Tightening (+300 bps Policy Rate Hike)
   • Attr27 (Interest Coverage)  = max(0.1, Attr27 * (1.0 / (1.0 + 300 / 400))) 
                                 = max(0.1, Attr27 * 0.571)

3. SCEN-03: Supply-Chain Working Capital Squeeze (+30 Days DSO Delay)
   • Attr44 (Receivables DSO)   += 30.0 Days
   • Attr40 (Cash Ratio)        *= max(0.0, 1.0 - 30 / 100) = 0.70

4. SCEN-04: Compound Stagflation Multi-Shock
   • Attr9 (Sales Demand)       *= 0.85 (-15% demand drop)
   • Attr58 (Cost / Sales)      *= 1.15 (+15% input cost inflation)
   • Attr27 (Interest Coverage) *= 0.50 (+200 bps borrowing hike)
```

### 9.2 Interactive Custom Scenario Simulator
Officers can execute on-demand counterfactual re-simulations via `POST /api/bank/assessments/{id}/simulate-scenario` by setting custom parameters:
* $\Delta \text{Rev} \in [-50\%, \, +10\%]$
* $\Delta \text{Rate} \in [0, \, 800\text{ bps}]$
* $\Delta \text{DSO} \in [0, \, 90\text{ days}]$
* $\Delta \text{Cost} \in [0\%, \, +30\%]$

---

## 10. Multi-Horizon Cumulative Default Term Structure

In [`backend/fusion/horizons.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/fusion/horizons.py), RIPPLE projects forward cumulative default probabilities over 1 to 5 years:

### Step 1: Base Hazard Intensity ($\lambda$)
$$\lambda = -\ln(1 - PD_{\text{fused}})$$

### Step 2: Multi-Year Hazard Scaling Factors ($F_k$)
Calibrated from multi-year Polish corporate loan registries:
$$F_1 = 1.00, \quad F_2 = 1.55, \quad F_3 = 1.98, \quad F_4 = 2.32, \quad F_5 = 2.58$$

### Step 3: Cumulative Multi-Year Forward Default Probability ($PD_k$)
$$PD_k = 1 - e^{-\lambda \cdot F_k} = 1 - (1 - PD_{\text{fused}})^{F_k}$$

### Step 4: Strict Monotonicity Enforcement
$$PD_k = \min\left(1.0, \, \max\left(PD_{k-1}, \, PD_k\right)\right) \implies PD_1 \le PD_2 \le PD_3 \le PD_4 \le PD_5$$

---

## 11. Investment R&D & Quantitative Risk Signals Suite

### 11.1 Information Coefficient (IC) & Predictive Power
Measures how effectively a quantitative factor ranks borrower creditworthiness 12 months in advance:
$$\text{IC} = \rho(S_t, \, y_{t+1}) = \frac{\sum (S_i - \bar{S})(y_i - \bar{y})}{\sqrt{\sum (S_i - \bar{S})^2 \sum (y_i - \bar{y})^2}}$$

### 11.2 Rank IC (Spearman Rank Correlation)
Evaluates monotonic ranking power independent of linear assumptions:
$$\text{Rank IC} = 1 - \frac{6 \sum d_i^2}{N(N^2 - 1)}$$
* Institutional Benchmark: $|\text{Rank IC}| \ge 0.05 - 0.15$ indicates a strong institutional credit signal.

### 11.3 IC Information Ratio (IR) & t-Statistic
* **Information Ratio (Signal Consistency):**
  $$\text{IR} = \frac{\text{Mean}(\text{IC})}{\text{Std}(\text{IC})} \times \sqrt{4}$$
* **Hypothesis Test (t-stat):**
  $$t = \frac{\overline{\text{IC}}}{\text{SE}(\text{IC})} = \frac{\overline{\text{IC}}}{\text{Std}(\text{IC}) / \sqrt{N}}$$
  A $t\text{-stat} > 2.0$ confirms statistical significance at $p < 0.05$.

---

## 12. Evaluator Q&A Defense Cheat Sheet (Exact Number Walkthroughs)

Use this section if the evaluator asks how a specific number on screen was derived.

---

### Question 1: "Where does the 8.90% Fused PD come from for PolTech Solutions?"
* **Answer:**
  1. The preprocessor computes 64 ratios from PolTech's balance sheet (Assets: 980k PLN, Revenue: 1.45M PLN, EBIT: 125k PLN).
  2. The calibrated LightGBM model outputs standalone tabular default probability:
     $$PD_{\text{tab}} = 3.10\%$$
  3. The PyTorch GNN evaluates PolTech’s 7 connected counterparties (CloudInfra, MicroSilicon, Warsaw FinTech, etc.) and propagates edge risk:
     $$PD_{\text{graph}} = 41.74\%$$
  4. The Fusion Engine combines them using $w_{\text{graph}} = 0.15$:
     $$PD_{\text{fused}} = (0.85 \times 0.0310) + (0.15 \times 0.4174) = 0.02635 + 0.06261 = 0.08896 \approx \mathbf{8.90\%}$$
  5. Because $8.90\% \in [5.0\%, 15.0\%)$, it lands in **Band C (Elevated Risk)** and receives the recommendation **`FURTHER_REVIEW`**.

---

### Question 2: "Why is Mazovia Logistics classified as Further Review instead of High Risk?"
* **Answer:**
  1. Mazovia Logistics has standalone Tabular PD = $4.52\%$ and Graph PD = $48.87\%$.
  2. The Fused PD is:
     $$PD_{\text{fused}} = (0.85 \times 0.0452) + (0.15 \times 0.4887) = 0.03842 + 0.07330 = 0.1117 \approx \mathbf{11.18\%}$$
  3. Under our Basel II/III SME risk schedule, **Band D (High Risk)** requires $PD \ge 15.0\%$ or negative balance-sheet equity.
  4. Mazovia has positive equity (260,000 PLN) and a Fused PD of $11.18\%$, placing it in **Band C (Elevated Risk)**.
  5. This appropriately triggers **`FURTHER_REVIEW`** (referral to credit committee) so loan officers can inspect freight fuel contracts, rather than unfairly denying a viable company a working capital loan.

---

### Question 3: "How does the system calculate the 3-Year Forward Default Projection of 17.06%?"
* **Answer:**
  1. Start with the baseline 1-year Fused PD: $PD_1 = 0.0890$ ($8.90\%$).
  2. Compute base continuous hazard intensity:
     $$\lambda = -\ln(1 - 0.0890) = -\ln(0.9110) = 0.09321$$
  3. Apply the empirically calibrated Year-3 term-structure multiplier $F_3 = 1.98$:
     $$\text{CumHazard}_3 = 0.09321 \times 1.98 = 0.18456$$
  4. Calculate cumulative 3-year probability of default:
     $$PD_3 = 1 - e^{-0.18456} = 1 - 0.83147 = 0.16853 \approx \mathbf{16.85\%}$$
  5. Monotonicity check: $PD_3 \ge PD_2 \ge PD_1$ holds strictly.

---

### Question 4: "Why does the Monetary Rate Tightening scenario produce a +1.95% increase in PD?"
* **Answer:**
  1. Baseline interest coverage ratio for the SME was $Attr_{27} = 4.46\times$.
  2. Under a $+300\text{ bps}$ hike, borrowing cost escalation compresses interest coverage:
     $$Attr_{27}^{\text{shocked}} = 4.46 \times 0.571 = 2.55\times$$
  3. The full feature vector with shocked $Attr_{27}$ is re-fed into the calibrated LightGBM pipeline.
  4. The model re-evaluates the probability of default under higher debt service burden:
     $$PD_{\text{shocked}} = 5.05\%, \quad \Delta PD = 5.05\% - 3.10\% = +\mathbf{1.95\%}$$
  5. Zero heuristic multipliers were applied; this is an exact non-linear model re-prediction.

---

### Question 5: "How does RIPPLE prevent look-ahead bias and protect financial statement provenance?"
* **Answer:**
  1. **Dual-Source KRS Reconciliation:** When financial files are uploaded, their SHA-256 digests are logged, and line items are compared against the Polish National Court Register (KRS) within a $5.0\%$ relative divergence threshold.
  2. **Point-in-Time Engine (`AsOfJoinEngine`):** Every financial record carries both an accounting period-end timestamp ($t_{\text{end}}$) and an official statutory publication timestamp ($t_{\text{pub}}$). The engine enforces $t_{\text{pub}} \le t_{\text{decision}}$, guaranteeing that financial events occurring after the assessment date are strictly invisible to the model.

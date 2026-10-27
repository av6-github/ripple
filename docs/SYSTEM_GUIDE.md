# RIPPLE — Comprehensive System & Architectural Guide

---

## 1. End-to-End Functional Flow (Data Lifecycle)

This section explains the exact journey of data through RIPPLE, from initial submission to the final credit officer decision, highlighting the backend actions performed at each stage.

```
[ Data Ingestion ] ──▶ [ Quality & Completeness ] ──▶ [ Feature Engineering ]
                                                              │
       ┌──────────────────────────────────────────────────────┴──────────────────────────────────────────────────────┐
       ▼                                                                                                             ▼
[ Calibrated Tabular XGBoost ]                                                                            [ 2-Layer GraphSAGE GNN ]
  - 64 Polish bankruptcy ratios                                                                             - Supply-chain ego-network
  - Isotonic probability calibration                                                                        - Counterparty contagion risk
       │                                                                                                             │
       └──────────────────────────────────────────────────────┬──────────────────────────────────────────────────────┘
                                                              ▼
                                                 [ Multi-Modal Risk Fusion ]
                                                   - 85% Tabular + 15% Graph
                                                   - Basel Risk Bands (A to D)
                                                              │
                                ┌─────────────────────────────┼─────────────────────────────┐
                                ▼                             ▼                             ▼
                      [ TreeSHAP Explainer ]       [ Term Structure & Stress ]    [ Quantitative R&D Suite ]
                        - Risk drivers               - 1–5 yr monotonic PD          - Point-in-Time As-Of join
                        - Mitigating factors         - 4 macro shock reruns         - Dual-source KRS reconciliation
                                                                                    - Cross-sectional ranking
                                                              │
                                                              ▼
                                                 [ Officer Custody & Audit ]
                                                   - Discretionary decision
                                                   - Override logging (Rule 4.6)
                                                   - Immutable snapshot in DB
                                                              │
                                ┌─────────────────────────────┴─────────────────────────────┐
                                ▼                                                           ▼
                      [ Bank Officer Portal ]                                     [ SME Borrower Portal ]
                        - Full risk dossier                                         - Redacted readiness status
                        - Printable committee memo                                  - Confidential (Rule 4.8)
```

### Stage 1: Data Sources & Ingestion
Data enters RIPPLE through three primary channels:
1. **Borrower Financial Statements**: Balance sheets, income statements, and cash flow statements submitted via the SME portal or uploaded by a bank officer in formats such as `.csv`, `.xlsx`, `.pdf`, or `.arff`.
2. **Alternative Data**: High-frequency bank account transaction ledgers (cash inflows/outflows) and trade credit payable/receivable invoice records.
3. **Commercial Supply Chain Graph**: Directed relationships (`SUPPLIES_TO`, `BUYS_FROM`) stored in Neo4j AuraDB representing commercial transactions with suppliers and customers.

*Backend Action*: Dedicated parsers (`CSVParser`, `XLSXParser`, `ARFFParser`) normalize heterogeneous accounting headers (e.g. mapping "Sales", "Turnover", or "Total Revenue" into a standardized `total_revenue` field).

### Stage 2: Data Quality & Completeness Verification Gate
Before any model receives data, it passes through automated verification gates:
- **Accounting Identity Verification**: Checks that fundamental identities hold within a $1.0\%$ tolerance:
  $$\text{Total Assets} = \text{Total Liabilities} + \text{Total Equity}$$
  $$\text{Working Capital} = \text{Current Assets} - \text{Short-Term Liabilities}$$
- **Boundary Checks**: Ensures assets $> 0$ and revenues $\ge 0$.
- **Completeness Evaluation (`CompletenessEvaluator`)**: Evaluates the ratio of present core financial fields. If data completeness is below $60.0\%$, the backend triggers an automated halt: no speculative probability of default (PD) is computed, and the assessment is marked `INCONCLUSIVE` (Rule 4.2).

### Stage 3: Feature Engineering & Leakage Protection
Once validated, the raw accounting statements are processed by the `FeatureEngine`:
- **Leakage Guard (`LeakageGuard`)**: Checks all input keys against forbidden target indicators (such as `charge_off`, `recovery`, `post_decision`, or `default_status`). Any post-prediction variable immediately raises a `TargetLeakageError` (Rule 4.5).
- **Ratio Computation**: Calculates canonical financial ratios (Liquidity, Solvency, Profitability, Operating Efficiency) and the **64 Polish bankruptcy attributes** (`Attr1` to `Attr64`) using safe division routines (`safe_div()`) to prevent division by zero or mathematical distortion from negative equity.
- **Alternative Data Extraction**: Computes monthly transaction velocity, inflow volume variability, on-time invoice settlement percentages, and Herfindahl-Hirschman concentration indices (HHI).

### Stage 4: Dual-Engine Machine Learning Scoring
The assessment snapshot is dispatched concurrently to two machine learning engines:
1. **Calibrated Tabular XGBoost Engine**: Analyzes the firm's financial statements and ratios, producing a baseline standalone probability of default (`tabular_pd`).
2. **PyTorch Geometric Graph Neural Network (GNN)**: Queries Neo4j AuraDB to extract the SME's 1-hop and 2-hop commercial ego-network, passing neighbor financial vectors through graph convolution layers to calculate network credit contagion (`graph_pd`).

### Stage 5: Multi-Modal Risk Fusion & Rating
The `FusionEngine` synthesizes the two signals:
- **Weighted Integration**:
  $$\text{Fused PD} = 0.85 \times \text{Tabular PD} + 0.15 \times \text{Graph PD}$$
- **Tabular Primacy Rule**: Graph influence is capped at $\le 50\%$ so that an SME with sound standalone financials cannot be denied credit purely due to external graph topology.
- **Cold-Start Policy**: If an SME has no recorded supply chain connections (`degree == 0`), the GNN gracefully triggers `is_cold_start = True`. RIPPLE falls back to $100\%$ tabular scoring without fabricating network risk.
- **Basel Rating Band Mapping**:
  - **Band A (Low Risk)**: $\text{PD} < 2.0\%$
  - **Band B (Moderate Risk)**: $2.0\% \le \text{PD} < 5.0\%$
  - **Band C (Elevated Risk)**: $5.0\% \le \text{PD} < 12.0\%$
  - **Band D (High Risk)**: $\text{PD} \ge 12.0\%$

### Stage 6: Explainability, Term Structure, & Stress Testing
- **Local Attribution (SHAP)**: Computes exact feature contributions using `TreeExplainer`, ranking the top risk drivers (pushing default up) and top mitigating factors (pulling default down).
- **Default Term Structure**: The `HorizonProjector` projects default risk monotonically across 1, 2, 3, 4, and 5-year horizons ($\text{PD}_1 \le \text{PD}_2 \le \dots \le \text{PD}_5$).
- **Macroeconomic Stress Scenarios**: Reruns the feature calculation and scoring model under 4 macroeconomic shocks (Revenue $-15\%$, Rate Hike $+300\text{ bps}$, Working Capital Squeeze $+15\text{ days DSO}$, and Stagflation) to measure balance sheet resilience.

### Stage 7: Quantitative R&D & Lineage Audit
The `QuantAnalyticsService` executes institutional risk controls:
- **Point-in-Time (PIT) As-Of Join**: Masks any disclosure published after the decision timestamp, verifying zero look-ahead bias.
- **Dual-Source Reconciliation**: Compares borrower self-reported data against official KRS registry data within a $5.0\%$ tolerance.
- **Cross-Sectional Normalization**: Ranks the SME's ratios into percentiles ($0\text{--}100\%$) relative to contemporaneous industry peers, applying winsorisation and OLS size-neutralisation.
- **Cryptographic Provenance**: Generates a bit-exact SHA-256 digest of input features and the physical model binary (`model_bundle.joblib`).

### Stage 8: Human Officer Decision, Governance & Storage
- **Decision Custody (Rule 4.6)**: RIPPLE is decision support, not an automated underwriter. The model outputs an advisory recommendation (`LOWER_RISK`, `FURTHER_REVIEW`, `HIGHER_RISK`, or `INCONCLUSIVE`).
- **Human Discretion & Overrides**: The bank officer enters an official decision (`APPROVE`, `REJECT`, `OVERRIDE_APPROVE`, `OVERRIDE_REJECT`). Any override requires mandatory justification text.
- **Persistence**: All inputs, predictions, explanations, and officer actions are saved as an immutable snapshot in remote PostgreSQL (Supabase) with full audit logging.

### Stage 9: Role-Based Presentation
- **Bank Officer View (`/bank/assessments/[id]`)**: Full dossier containing multi-modal probabilities, SHAP charts, interactive ego-network, stress test cards, quant R&D suite, and printable committee memo.
- **SME View (`/sme`)**: A clean readiness overview (`ADEQUATE` vs `REQUIRES_ATTENTION`) and actionable guidance. **Completely redacts** internal bank PD, credit committee notes, and proprietary model thresholds (Rule 4.8).

---

## 2. Machine Learning Deep-Dive: XGBoost, GNN, and SHAP

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               MACHINE LEARNING TRIFECTA                                │
├──────────────────────────┬─────────────────────────────┬───────────────────────────────┤
│         XGBOOST          │             GNN             │             SHAP              │
│    (Tabular Primacy)     │     (Network Contagion)     │     (Model Transparency)      │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ Evaluates 64 accounting  │ Evaluates 1- & 2-hop        │ Breaks down XGBoost decisions │
│ ratios to predict        │ commercial trade partners   │ into exact dollar/ratio       │
│ standalone bankruptcy.   │ in Neo4j supply chain graph.│ marginal contributions.       │
│ Calibrated via Isotonic  │ GraphSAGE aggregates        │ Guarantees fair, explainable, │
│ Regression for empirical │ counterparty credit         │ and auditable committee       │
│ default probabilities.   │ distress into graph_pd.     │ recommendations.              │
└──────────────────────────┴─────────────────────────────┴───────────────────────────────┘
```

### 2.1 XGBoost (Extreme Gradient Boosting)
*Implemented in `backend/ml/xgboost_model.py` and trained via `backend/ml/train_tabular.py`*

#### What It Is
XGBoost is an optimized distributed gradient boosting library that constructs an ensemble of shallow decision trees. Rather than training independent trees in parallel (like a Random Forest), XGBoost builds trees sequentially. Each new tree fits to the negative gradient (the pseudo-residuals) of the loss function evaluated on the prior ensemble's predictions.

#### Why It Is Used in RIPPLE
- **Tabular Superiority**: For structured financial ratio tables, tree-based boosting consistently outperforms deep neural networks.
- **Non-Linear Interactions & Thresholds**: Solvency risks are non-linear; for instance, high leverage is manageable with strong liquidity, but catastrophic when liquidity evaporates. Decision trees naturally capture these threshold interactions.
- **Sparsity-Aware Split Finding**: Handles missing financial fields by learning a default routing direction at each split.

#### Configuration in This Project
- **Class Imbalance Management**: SME bankruptcy datasets are heavily skewed (~14:1 non-bankrupt to bankrupt). We set:
  $$\text{scale\_pos\_weight} = \frac{N_{\text{negative}}}{N_{\text{positive}}} \approx 13.4$$
  This penalizes false negatives (missing a defaulting borrower) more heavily than false positives.
- **Hyperparameters**:
  - `max_depth = 4`: Restricts tree depth to prevent memorizing idiosyncrasies.
  - `learning_rate = 0.05` & `n_estimators = 150`: Slow learning rate with sufficient trees for smooth convergence.
  - `subsample = 0.8` & `colsample_bytree = 0.8`: Stochastic feature and instance sampling for regularisation.
- **Isotonic Probability Calibration (`backend/ml/calibrator.py`)**:
  Raw XGBoost margin outputs represent uncalibrated ranking scores. We apply 5-fold cross-validated **Isotonic Regression** to calibrate predictions into true empirical probabilities:
  $$\mathbb{P}(\text{Default} \mid \text{Score} = p) \approx p$$
  Achieves a Brier score of **$0.029$** and ROC-AUC of **$0.9507$** on the test holdout set.

---

### 2.2 Graph Neural Network (GNN — GraphSAGE / GCN)
*Implemented in `backend/graph/gnn_model.py` and coordinated via `backend/graph/gnn_service.py`*

#### What It Is
Graph Neural Networks operate on graph topologies where entities are represented as nodes connected by relational edges. GNNs use **neighborhood message passing**: a node iteratively aggregates the feature representations of its immediate neighbors, combines them with its own state, and applies non-linear transformations.

#### Why It Is Used in RIPPLE
SMEs do not fail in isolation. If an automotive manufacturer's primary buyer defaults, the manufacturer faces immediate cash-flow distress. Standard models cannot see this vulnerability because the manufacturer's historical statements may still look healthy. The GNN provides a **Network Contagion Probability (`graph_pd`)** based on counterparty health.

#### Architecture in This Project
Built using **PyTorch Geometric (`torch_geometric`)**:
1. **Input Vector ($X_v \in \mathbb{R}^{67}$)**:
   Each SME node is assigned its 64 Polish financial attributes plus 3 missingness indicator flags.
2. **Layer 1 (`GCNConv(67 -> 32)`)**:
   Aggregates 1-hop neighbor features using normalized adjacency:
   $$H^{(1)} = \text{ReLU}\left( \text{BatchNorm}\left( \tilde{D}^{-\frac{1}{2}} \tilde{A} \tilde{D}^{-\frac{1}{2}} X W^{(0)} \right) \right)$$
   Applies Dropout ($p = 0.20$) for regularisation.
3. **Layer 2 (`GCNConv(32 -> 16)`)**:
   Aggregates 2-hop contagion (e.g. distress at a supplier's supplier), outputting a compact 16-dimensional structural embedding.
4. **Classification Head**:
   A `Linear(16 -> 2)` projection with Softmax outputs `graph_pd` $\in [0.0, 1.0]$.
5. **Cold-Start Fallback (Rule 4.2)**:
   If an SME is an isolated node with zero commercial edges in Neo4j, the system sets `is_cold_start = True`, bypasses the GNN, and relies 100% on the tabular model.

---

### 2.3 SHAP (SHapley Additive exPlanations)
*Implemented in `backend/fusion/explainer.py`*

#### What It Is
SHAP is an axiomatic, game-theoretic method for explaining model predictions. Originating from cooperative game theory (Lloyd Shapley), a Shapley value quantifies the marginal contribution of each player (feature) to the final payoff (model prediction), averaged over all possible feature coalitions:
$$\phi_i = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|! (|F| - |S| - 1)!}{|F|!} \left[ f(S \cup \{i\}) - f(S) \right]$$

#### Why It Is Used in RIPPLE
Modern banking regulations (e.g. EU AI Act, Basel Committee standards, Fair Lending rules) prohibit unexplainable "black-box" credit rejections. If an SME is assigned elevated risk, the credit officer must know exactly which financial deficiencies caused that score.

#### How It Operates in This Project
- **TreeSHAP Algorithm**: Leverages the fast $O(T L D^2)$ tree-structure exploitation algorithm to compute exact Shapley values directly across XGBoost tree ensembles.
- **Isolation Rule (Rule 4.7)**:
  > **SHAP applies exclusively to the tabular model. SHAP is NEVER described as explaining the GNN.** GNN network risk is explained separately using graph topology metrics (in/out-degree, counterparty status).
- **Human-Readable Decomposition**:
  Maps raw Polish codes (`Attr1` to `Attr64`) into plain-English labels. The explainer groups results into:
  - **Top Risk Drivers**: Features with the largest positive SHAP values (pushing PD up, e.g. high short-term debt).
  - **Top Mitigating Factors**: Features with negative SHAP values (pulling PD down, e.g. robust gross margins).

---

## 3. Prominent Usage of Pandas, NumPy, and SQL/Databases

### 3.1 NumPy (`numpy`)
NumPy is used throughout the backend for vectorized numerical operations, safe financial math, distribution sampling, and array manipulation:

| Location | Specific Usage | Purpose & Implementation |
|---|---|---|
| `backend/features/financial_ratios.py` | `safe_div()`, `np.clip` | Prevents divide-by-zero crashes using float epsilon ($1\times 10^{-9}$) and clamps ratio blowups (e.g., capping debt-to-equity at $+50.0$ when equity is negative). |
| `backend/quant/signals.py` | `np.percentile`, `np.clip` | **Outlier Winsorisation**: Truncates ratio series at the 1st and 99th percentiles to protect gradient splits from extreme outliers. |
| `backend/quant/signals.py` | `np.linalg.pinv`, matrix dot products | **OLS Feature Neutralisation**: Solves $w = (X^T X)^{-1} X^T y$ and computes residuals $y_{\text{neutral}} = y - Xw$ to strip out sector and company size bias. |
| `backend/quant/analytics_service.py` | `np.random.uniform`, `np.random.normal` | Generates realistic, reproducible synthetic variance ($\pm 1.5\%$) for dual-source KRS reconciliation and cross-sectional peer distributions anchored on SME metrics. |
| `backend/graph/gnn_service.py` | `torch.tensor(..., dtype=torch.float32)` | Converts raw NumPy feature matrices into contiguous PyTorch float tensors for GNN message passing. |

---

### 3.2 Pandas (`pandas`)
Pandas manages tabular data transformations, time-series operations, cross-sectional cohort ranking, and point-in-time merges:

| Location | Specific Usage | Purpose & Implementation |
|---|---|---|
| `backend/ml/data_loader.py` | `pd.DataFrame`, `.dropna()`, `.astype()` | Loads and parses Polish bankruptcy ARFF files, normalizes 64 feature columns, separates the binary target, and splits training/test cohorts. |
| `backend/quant/signals.py` | `.groupby()`, `.rank(pct=True)` | **Cross-Sectional Ranking**: Groups firms by NACE sector code and computes exact uniform percentile ranks ($[0.0, 1.0]$) for financial signals. |
| `backend/quant/signals.py` | `.rolling(window=w).std()`, `.expanding().min()` | **Rolling & Expanding Risk**: Calculates trailing volatility of operating cash flows and expanding minimum liquidity headroom over multi-period financial histories. |
| `backend/quant/pit_join.py` | `pd.merge_asof(..., direction="backward")` | **Point-in-Time Join**: Merges accounting statements with evaluation timestamps using backward-looking matching on `publication_date <= decision_date`, enforcing zero look-ahead bias. |
| `backend/services/parsers/csv_parser.py` | `pd.read_csv()`, `.rename(columns=...)` | Ingests borrower uploads, executes column synonym mapping, and validates numerical types. |

---

### 3.3 SQL & Database Architecture (Supabase PostgreSQL + Neo4j AuraDB)
Persistence is split between a relational database for transactional integrity and a graph database for network topologies (Rule 4.1: Remote Persistence Only).

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               PERSISTENCE ARCHITECTURE                                 │
├──────────────────────────────────────────┬─────────────────────────────────────────────┤
│         SUPABASE (PostgreSQL 15)         │              NEO4J AURADB                   │
│          Relational & Audit Log          │          Commercial Graph Engine            │
├──────────────────────────────────────────┼─────────────────────────────────────────────┤
│ • 14 relational tables (sme, assessment, │ • Nodes: (:SME {id, name, sector})          │
│   input_snapshot, prediction, etc.)      │ • Edges: [:SUPPLIES_TO], [:BUYS_FROM]       │
│ • JSONB input & explanation storage      │ • Attributes: annual_volume, tenure_months  │
│ • Foreign key cascades & CHECK bounds    │ • Synthetic disclosure: is_synthetic = true │
│ • Row-Level Security (RLS) policies      │ • Subgraph Cypher pattern extraction        │
└──────────────────────────────────────────┴─────────────────────────────────────────────┘
```

#### Supabase PostgreSQL (Relational Engine)
- **Schema & Migrations (`infra/migrations/001_initial_schema.sql`)**:
  Contains 14 normalized tables:
  - `sme`: Master corporate entity records (tax ID, sector, registration date).
  - `financial_record`: Annual/quarterly statement metrics with mandatory provenance columns (`source_type`, `confidence`).
  - `assessment`: Lifecycle state, overall confidence, fused PD, risk band, and officer decision.
  - `assessment_input_snapshot`: Complete, immutable JSONB copy of the input financial payload at decision time.
  - `prediction`: Horizon-specific default estimates (12 to 60 months).
  - `explanation`: Serialized SHAP values and top risk/mitigating drivers.
  - `scenario_result`: Macroeconomic stress test outcomes.
  - `audit_log`: Append-only compliance log recording officer overrides and justifications.
- **Repository Pattern (`AssessmentRepository`, `FinancialRepository`)**:
  - Uses `psycopg2` with parameterized queries (`%s`) to eliminate SQL injection vulnerabilities.
  - Handles transaction boundaries with automatic rollbacks on failure.
  - Implements a resilient connection string fallback: checks `SUPABASE_DB_URL` followed by `DATABASE_URL`.
- **Row-Level Security (RLS) (`infra/migrations/002_rls_policies.sql`)**:
  Enforces tenant isolation: `sme_user` accounts can only query their own submitted statements, while `bank_officer` roles have read access to portfolio assets and write access to decision logs.

#### Neo4j AuraDB (Graph Engine)
- **Cypher Query Execution (`backend/graph/neo4j_client.py`)**:
  Connects over encrypted TLS Bolt connections (`neo4j+s://...`).
- **Graph Schema**:
  - Nodes: `(:SME {sme_id, legal_name, sector, country})`
  - Relationships: `(:SME)-[:SUPPLIES_TO {annual_volume, tenure_months, is_synthetic}]->(:SME)`
- **Ego-Network Extraction**:
  Extracts 1-hop and 2-hop subgraphs for any target SME to build adjacency matrices for PyTorch Geometric GNN inference.
- **Rule 4.4 Enforcement**: Every synthetic commercial relationship is persisted with property `is_synthetic: true`.

---

## 4. Complete Technology Stack

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              RIPPLE COMPLETE TECH STACK                                │
├──────────────────────────┬─────────────────────────────────────────────────────────────┤
│ Frontend Framework       │ Next.js 16.3.5 (App Router, Turbopack, Server/Client Comps)│
│ Frontend Core & Language │ React 19.2.8, TypeScript 5, Node.js 20 LTS                  │
│ Styling & UI Components  │ Tailwind CSS v4, Lucide React Icons                         │
│ API Client & State       │ Native Fetch API, Custom React Context (`AuthContext`)      │
├──────────────────────────┼─────────────────────────────────────────────────────────────┤
│ Backend API Engine       │ FastAPI 0.141.1, Uvicorn 0.53.0 (ASGI, Event Loop)          │
│ Language & Runtime       │ Python 3.12 (Strict typing, async context lifespans)        │
│ Schema & Validation      │ Pydantic v2 (2.13.5), Pydantic Settings                     │
│ Security & Auth          │ PyJWT 2.14.0 (HMAC-SHA256, RBAC), Python-Multipart          │
├──────────────────────────┼─────────────────────────────────────────────────────────────┤
│ Tabular Machine Learning │ XGBoost 3.4.1, Scikit-Learn 1.9.1 (Isotonic, Pipelines)     │
│ Graph Machine Learning   │ PyTorch 2.14.0 (CPU), PyTorch Geometric (`torch_geometric`)│
│ Model Explainability     │ SHAP 0.52.0 (`TreeExplainer`)                               │
│ Data Science & Math      │ NumPy 2.5.3, Pandas 3.0.6, SciPy 1.18.1                     │
│ File Parsers             │ OpenPyXL 3.1.5 (Excel), LIAC-ARFF (ARFF datasets)          │
├──────────────────────────┼─────────────────────────────────────────────────────────────┤
│ Relational Database      │ Supabase (Remote PostgreSQL 15, Transactional Persistence)  │
│ Database Drivers         │ Psycopg2-binary 2.9.13                                      │
│ Graph Database           │ Neo4j AuraDB (Bolt Protocol, Cypher Engine, neo4j 6.3.1)    │
│ Supporting Cloud Services│ Pinecone (Vector Embeddings), Upstash Redis, Cloudinary     │
├──────────────────────────┼─────────────────────────────────────────────────────────────┤
│ DevOps & Virtualisation  │ Docker, Docker Compose, Multi-stage alpine/slim builds      │
│ Continuous Integration   │ GitHub Actions CI (Automated Pytest & Next.js Build Gates)  │
│ Test Harness             │ Pytest 9.1.1 (with ROS plugin isolation)                    │
│ Code Quality & Linting   │ ESLint 9 (Flat Config), Python Type Hints                   │
└──────────────────────────┴─────────────────────────────────────────────────────────────┘
```

# RIPPLE — Technical Architecture & End-to-End Data Flow Manual
**Date:** October 2026  
**Audience:** Software Engineers, ML Engineers, Quant Researchers, Credit Risk Architects  
**Purpose:** Comprehensive technical walkthrough explaining technologies, algorithms, and data flows with direct code-file references.

---

## 1. System Topology & Technology Stack

RIPPLE employs a decoupled distributed architecture:

```
[ Next.js 16 SPA (React 19) ]
         │
         │ REST / HTTPS (Bearer JWT HS256)
         ▼
[ FastAPI Gateway API (Python 3.12) ]
   ├── [ Authentication & RBAC ] ──▶ PostgreSQL (app_user)
   ├── [ Parsers & Ingestion ] ────▶ Normalization & Validation Gate
   ├── [ Feature Engine ] ─────────▶ 64 Polish Ratios + Leakage Guard
   ├── [ Tabular ML ] ─────────────▶ Calibrated XGBoost + Isotonic Regression
   ├── [ Graph Neural Network ] ───▶ 2-Layer GraphSAGE (Neo4j / PostgreSQL mirror)
   ├── [ Multimodal Fusion ] ──────▶ Weighted Fusion & Basel Rating Bands
   ├── [ TreeSHAP Explainer ] ─────▶ Local Shapley Factor Attributions
   ├── [ Scenario Engine ] ────────▶ Macroeconomic Stress Re-Scoring
   ├── [ Quant R&D Engine ] ───────▶ Point-in-Time Joins & KRS Reconciliation
   └── [ Persistence Repositories ]▶ Remote Supabase PostgreSQL (11 tables)
```

| Layer | Subsystem | Technology | Code File References |
| :--- | :--- | :--- | :--- |
| **Frontend** | Application Router | Next.js 16.3.5 (Turbopack) | [`app/layout.tsx`](file:///home/atharv-vedant/PROJECTS/ripple/app/layout.tsx), [`app/page.tsx`](file:///home/atharv-vedant/PROJECTS/ripple/app/page.tsx) |
| **Frontend** | Session & Auth | React Context + LocalStorage | [`lib/auth-context.tsx`](file:///home/atharv-vedant/PROJECTS/ripple/lib/auth-context.tsx), [`app/components/RoleGuard.tsx`](file:///home/atharv-vedant/PROJECTS/ripple/app/components/RoleGuard.tsx) |
| **Frontend** | API Client | Fetch API (typed wrapper) | [`lib/api.ts`](file:///home/atharv-vedant/PROJECTS/ripple/lib/api.ts), [`lib/types.ts`](file:///home/atharv-vedant/PROJECTS/ripple/lib/types.ts) |
| **Gateway** | API Routing | FastAPI + Starlette + Uvicorn | [`backend/main.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/main.py), [`backend/api/routers/`](file:///home/atharv-vedant/PROJECTS/ripple/backend/api/routers) |
| **Security** | Auth & Encryption | PBKDF2-HMAC-SHA256 + PyJWT | [`backend/api/auth.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/api/auth.py), [`backend/repositories/user_repository.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/repositories/user_repository.py) |
| **Ingestion** | Document Parsers | pandas, openpyxl, re | [`backend/parsers/`](file:///home/atharv-vedant/PROJECTS/ripple/backend/parsers), [`backend/services/ingestion_service.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/services/ingestion_service.py) |
| **Validation**| Completeness Gate | Pydantic v2 + Python standard | [`backend/validation/`](file:///home/atharv-vedant/PROJECTS/ripple/backend/validation) |
| **Features**  | Financial Engineering | NumPy + safe math | [`backend/features/feature_engine.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/features/feature_engine.py), [`backend/features/leakage_guard.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/features/leakage_guard.py) |
| **ML Engine** | Tabular Gradient Boost | XGBoost 2.x + Scikit-Learn | [`backend/ml/tabular_model.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/ml/tabular_model.py), [`backend/ml/calibration.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/ml/calibration.py) |
| **Graph ML**  | Supply Chain Contagion | PyTorch 2.6 + PyTorch Geometric | [`backend/graph/gnn_service.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/graph/gnn_service.py), [`backend/graph/neo4j_client.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/graph/neo4j_client.py) |
| **Explainability** | Tabular Attribution | SHAP (TreeExplainer) | [`backend/ml/shap_explainer.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/ml/shap_explainer.py) |
| **Scenario**  | Stress Testing Engine | Mathematical perturbation | [`backend/features/scenario_engine.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/features/scenario_engine.py) |
| **Quant R&D** | PIT Joins & Audit | Polars / pandas / NumPy | [`backend/quant/`](file:///home/atharv-vedant/PROJECTS/ripple/backend/quant) |
| **Database**  | Relational Persistence | Supabase PostgreSQL (`psycopg2`) | [`backend/repositories/`](file:///home/atharv-vedant/PROJECTS/ripple/backend/repositories), [`infra/migrations/`](file:///home/atharv-vedant/PROJECTS/ripple/infra/migrations) |

---

## 2. End-to-End Data Flow (Step-by-Step)

```
[ 1. User Upload / Form ] ──────▶ [ 2. Parser Normalization ] ──────▶ [ 3. Validation Gate ]
                                                                             │
    ┌────────────────────────────────────────────────────────────────────────┘
    ▼
[ 4. FeatureEngine (64 Ratios) ] ──▶ [ LeakageGuard Check ]
    │
    ├───▶ [ 5. Tabular XGBoost + Isotonic Calibrator ] ──▶ Standalone Tabular PD
    │
    ├───▶ [ 6. Graph Query (Neo4j / Postgres) + GNN ] ──▶ Contagion Graph PD
    │
    ▼
[ 7. FusionEngine (0.85/0.15 Blend) ] ──▶ Fused Multi-Modal PD & Basel Rating Band
    │
    ├───▶ [ 8. TreeSHAP Attribution ] ────────▶ Top 5 Risk Drivers & Mitigating Factors
    │
    ├───▶ [ 9. Term Structure & Scenarios ] ──▶ 1–5 Year Hazard Curve & 4 Macro Shocks
    │
    ├───▶ [ 10. Quant R&D Audit ] ────────────▶ PIT As-Of Join & KRS Reconciliation
    │
    ▼
[ 11. Immutable Snapshot in PostgreSQL ] ──▶ Credit Officer Decision & Printable Memo
```

---

### Step 1: User Submission & Ingestion Pipeline
- **Files Involved**:
  - Frontend: [`app/sme/upload/page.tsx`](file:///home/atharv-vedant/PROJECTS/ripple/app/sme/upload/page.tsx), [`lib/api.ts:uploadFinancialFile`](file:///home/atharv-vedant/PROJECTS/ripple/lib/api.ts#L170-L195)
  - Backend Router: [`backend/api/routers/sme_router.py:upload_financial_statement`](file:///home/atharv-vedant/PROJECTS/ripple/backend/api/routers/sme_router.py#L36-L80)
  - Service: [`backend/services/ingestion_service.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/services/ingestion_service.py)
  - Parsers: [`backend/parsers/csv_parser.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/parsers/csv_parser.py), [`backend/parsers/xlsx_parser.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/parsers/xlsx_parser.py), [`backend/parsers/arff_parser.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/parsers/arff_parser.py)
  - Repository: [`backend/repositories/financial_repository.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/repositories/financial_repository.py)

**Data Journey**:
1. The user drags a file into the upload zone or selects a 1-click sample preset (e.g. `healthy_tech_sme.csv`).
2. The browser constructs a `FormData` object containing the file binary and optional target `sme_id`.
3. `POST /api/sme/upload` receives the file. The router verifies borrower tenant isolation (Rule 4.8): if the caller is an SME user, it enforces that `sme_id` corresponds to the caller's authorized company.
4. `FinancialRepository.create_ingestion_job()` creates a tracking record in the `ingestion_job` table with status `PROCESSING`.
5. `IngestionService.process_file_upload()` identifies the file MIME type/extension and delegates to the appropriate parser:
   - `CSVParser`: Normalizes accounting headers by fuzzy synonym matching (e.g., `"Sales"`, `"Revenues"`, `"Przychody"` $\to$ `total_revenue`).
   - `XLSXParser`: Inspects multi-tab spreadsheets for Balance Sheet and Profit & Loss worksheets.
6. Financial line items are structured into `FinancialStatementData` with non-nullable provenance metadata (`source_type = "extracted_file"`, `confidence = "verified"`, `source_ref = filename`).
7. `FinancialRepository.save_financial_records()` commits raw statements into the `financial_record` table.

---

### Step 2: Quality & Completeness Verification Gate
- **Files Involved**:
  - [`backend/validation/accounting_identities.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/validation/accounting_identities.py)
  - [`backend/validation/completeness_evaluator.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/validation/completeness_evaluator.py)

**Data Journey**:
1. **Accounting Identity Validation**: The statements are checked against foundational accounting constraints:
   $$\Delta_{\text{Balance}} = \left| \text{Total Assets} - (\text{Total Liabilities} + \text{Total Equity}) \right|$$
   $$\text{Tolerance} = 0.01 \times \text{Total Assets}$$
   If $\Delta_{\text{Balance}} > \text{Tolerance}$, a `BALANCE_SHEET_UNBALANCED` data quality violation is logged.
2. **Completeness Evaluation**: `CompletenessEvaluator` checks for the presence of 10 essential financial fields:
   $$\text{Completeness Score} = \frac{\sum_{i=1}^{10} \mathbb{I}(\text{field}_i \text{ is present})}{10} \times 100\%$$
3. **Completeness Gate (Rule 4.2)**: If completeness is $< 60.0\%$, the assessment halts immediately and returns `INCONCLUSIVE`. No model inference is executed.

---

### Step 3: Feature Engineering & Target Leakage Prevention
- **Files Involved**:
  - [`backend/features/feature_engine.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/features/feature_engine.py)
  - [`backend/features/domain.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/features/domain.py)
  - [`backend/features/leakage_guard.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/features/leakage_guard.py)

**Data Journey**:
1. **Leakage Verification**: `LeakageGuard.audit_keys(feature_dict)` inspects feature dictionary keys against blacklisted forward-looking target indicators (`charge_off`, `recovery`, `post_decision`, `default_status`, `delinquency_event`). If any forbidden key exists, it raises `TargetLeakageError`, returning HTTP 422.
2. **Financial Ratio Computation**: Calculates canonical ratios:
   - Current Ratio $= \text{Current Assets} / \text{Short-Term Liabilities}$
   - Debt-to-Equity $= \text{Total Liabilities} / \text{Total Equity}$
   - ROA $= \text{Net Profit} / \text{Total Assets}$
   - Operating Cash Flow Ratio $= \text{OCF} / \text{Total Liabilities}$
3. **64 Polish Bankruptcy Ratios (`Attr1` to `Attr64`)**: Computes attributes including:
   - `Attr1`: Net Profit / Total Assets
   - `Attr2`: Total Liabilities / Total Assets
   - `Attr3`: Working Capital / Total Assets
   - `Attr9`: Total Sales / Total Assets
   - `Attr24`: Gross Profit (3-year) / Total Assets
   - `Attr46`: (Current Assets - Inventory) / Short-Term Liabilities
4. All division operations execute via `safe_div(numerator, denominator, default=0.0)` to eliminate zero-division runtime crashes.

---

### Step 4: Standalone Tabular Machine Learning Scoring
- **Files Involved**:
  - Model Inference: [`backend/ml/tabular_model.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/ml/tabular_model.py)
  - Calibration: [`backend/ml/calibration.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/ml/calibration.py)
  - Artifacts: `artifacts/models/tabular/v1.0.0/`

**Data Journey**:
1. The 64-dimensional feature vector is structured into a numeric array aligned with `artifacts/models/tabular/v1.0.0/metadata.json`.
2. Missing ratio values are imputed using offline training medians.
3. The feature array is passed to the trained **XGBoost Classifier**:
   $$\hat{y}_{\text{raw}} = \text{XGBoost.predict\_proba}(X)[:, 1]$$
4. **Isotonic Probability Calibration**: Raw decision tree probabilities are mapped through the fitted isotonic regression calibrator:
   $$\text{Tabular PD} = \text{IsotonicCalibrator.predict}(\hat{y}_{\text{raw}})$$
5. This maps uncalibrated tree margins to true empirical default frequencies.

---

### Step 5: Commercial Supply-Chain Contagion Diffusion
- **Files Involved**:
  - Neo4j Client: [`backend/graph/neo4j_client.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/graph/neo4j_client.py)
  - GNN Model: [`backend/graph/gnn_service.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/graph/gnn_service.py)
  - Relational Graph Fallback: [`backend/repositories/assessment_repository.py:get_counterparties_from_db`](file:///home/atharv-vedant/PROJECTS/ripple/backend/repositories/assessment_repository.py#L125-L175)

**Data Journey**:
1. `Neo4jGraphClient.get_ego_network(sme_id, hops=2)` executes a Cypher query to retrieve commercial suppliers (`SUPPLIES`), buyers (`SELLS_TO`), and partners (`TRANSACTS_WITH`).
2. **Dual-Store Resilience**: If Neo4j is offline or sleeping, `AssessmentRepository.get_counterparties_from_db()` queries the PostgreSQL `relationship` table, ensuring the borrower's $\ge 5$ counterparty graph is retrieved without failure.
3. **Graph Feature Tensor**: Node feature matrix $X \in \mathbb{R}^{N \times F}$ is populated with counterparty financial profiles; adjacency matrix $A$ represents directed trade volume edges.
4. **2-Layer GraphSAGE Message Passing**:
   $$h_v^{(1)} = \text{ReLU}\left( W_1 \cdot \text{MEAN}\left(\{h_u^{(0)}, u \in \mathcal{N}(v) \cup \{v\}\}\right) \right)$$
   $$h_v^{(2)} = \sigma\left( W_2 \cdot \text{MEAN}\left(\{h_u^{(1)}, u \in \mathcal{N}(v) \cup \{v\}\}\right) \right)$$
   $$\text{Graph PD} = h_{\text{target}}^{(2)}$$
5. **Cold-Start Policy**: If an SME has no recorded commercial trade counterparties ($\text{degree} = 0$), the service marks `is_cold_start = True`, falling back to 100% tabular scoring without fabricating relationships (Rule 4.2).

---

### Step 6: Multi-Modal Risk Fusion & Basel Rating Bands
- **Files Involved**:
  - [`backend/services/assessment_service.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/services/assessment_service.py)

**Data Journey**:
1. `AssessmentService.run_assessment()` invokes both the tabular engine and the graph engine.
2. **Weighted Fusion**:
   $$\text{Fused PD} = 0.85 \times \text{Tabular PD} + 0.15 \times \text{Graph PD}$$
3. **Tabular Primacy Cap**: If network distress is elevated, graph influence is bounded:
   $$\text{Graph Influence} \le 0.50 \times \text{Fused PD}$$
4. **Basel Rating Band Mapping**:
   - $\text{Fused PD} < 2.0\% \implies \textbf{Band A (Low Risk)}$, Recommendation: `LOWER_RISK`
   - $2.0\% \le \text{Fused PD} < 5.0\% \implies \textbf{Band B (Moderate Risk)}$, Recommendation: `LOWER_RISK`
   - $5.0\% \le \text{Fused PD} < 12.0\% \implies \textbf{Band C (Elevated Risk)}$, Recommendation: `FURTHER_REVIEW`
   - $\text{Fused PD} \ge 12.0\% \implies \textbf{Band D (High Risk)}$, Recommendation: `HIGHER_RISK`

---

### Step 7: Local Tabular Explainability (TreeSHAP)
- **Files Involved**:
  - [`backend/ml/shap_explainer.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/ml/shap_explainer.py)

**Data Journey**:
1. `ShapExplainer.explain(feature_vector)` executes `shap.TreeExplainer(model)` on the XGBoost tree ensemble.
2. Generates exact Shapley values $\phi_i$ satisfying the local efficiency property:
   $$\sum_{i=1}^{M} \phi_i = f(x) - \mathbb{E}[f(x)]$$
3. Categorizes factors:
   - **Primary Risk Drivers**: Features with $\phi_i > 0$ sorted descending (e.g. high short-term liabilities, negative net profit).
   - **Mitigating Factors**: Features with $\phi_i < 0$ sorted ascending (e.g. strong operating cash flow, high equity ratio).
4. Maps feature codes to human-readable accounting labels and formats contribution magnitudes for the UI.

---

### Step 8: Multi-Horizon Term Structure & Macroeconomic Stress Scenarios
- **Files Involved**:
  - [`backend/features/scenario_engine.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/features/scenario_engine.py)
  - [`backend/services/assessment_service.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/services/assessment_service.py)

**Data Journey**:
1. **Multi-Horizon Curves**: Calculates 1-year through 5-year cumulative default probabilities using monotonic hazard rate progression:
   $$\text{PD}_{1\text{yr}} = \text{Fused PD}$$
   $$\text{PD}_{2\text{yr}} = \min(1.0, \text{Fused PD} \times 1.55)$$
   $$\text{PD}_{3\text{yr}} = \min(1.0, \text{Fused PD} \times 1.98)$$
   $$\text{PD}_{4\text{yr}} = \min(1.0, \text{Fused PD} \times 2.32)$$
   $$\text{PD}_{5\text{yr}} = \min(1.0, \text{Fused PD} \times 2.58)$$
2. **Macroeconomic Stress Scenarios**: Rather than applying arbitrary multipliers to the output PD, `ScenarioEngine` perturbs the balance sheet line items and re-runs the full feature extraction and scoring pipeline:
   - *Interest Rate Shock*: $\text{Interest Expense} \gets \text{Interest Expense} + (0.03 \times \text{Total Liabilities})$
   - *Revenue Contraction*: $\text{Total Revenue} \gets \text{Total Revenue} \times 0.80$
   - *Inflation Cost Shock*: $\text{COGS} \gets \text{COGS} \times 1.15$
   - *Supply Chain Disruption*: $\text{Accounts Payable} \gets \text{Accounts Payable} \times 1.30$

---

### Step 9: Quantitative R&D & Backtesting Engine
- **Files Involved**:
  - [`backend/quant/pit_join.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/quant/pit_join.py)
  - [`backend/quant/reconciliation.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/quant/reconciliation.py)
  - [`backend/quant/ranking.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/quant/ranking.py)

**Data Journey**:
1. **Point-in-Time (PIT) As-Of Join**: Reconstructs information state at historical decision dates $T_{\text{decision}}$, rejecting filings stamped with $T_{\text{filing}} > T_{\text{decision}}$ to prevent look-ahead bias.
2. **KRS Registry Reconciliation**: Compares internal uploaded statements against Polish National Court Register (KRS) registry balances, flagging discrepancies $> 2.0\%$.
3. **Cross-Sectional Ranking**: Computes empirical percentiles against industry peer cohorts.

---

### Step 10: Human Officer Custody & Audit Trail
- **Files Involved**:
  - [`backend/repositories/assessment_repository.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/repositories/assessment_repository.py)
  - [`app/bank/assessments/[id]/page.tsx`](file:///home/atharv-vedant/PROJECTS/ripple/app/bank/assessments/[id]/page.tsx)
  - [`app/bank/assessments/[id]/report/page.tsx`](file:///home/atharv-vedant/PROJECTS/ripple/app/bank/assessments/[id]/report/page.tsx)

**Data Journey**:
1. All inputs, outputs, models, and SHAP factors are saved to `assessment_snapshot` in PostgreSQL with a unique UUID.
2. When the bank credit officer submits a discretionary decision (`APPROVE`, `REJECT`, `OVERRIDE_APPROVE`, `OVERRIDE_REJECT`), it is recorded into `officer_decision` with `officer_id`, `decision`, `is_override`, `override_reason`, and `comments`.
3. Navigating to `/bank/assessments/[id]/report` renders the formal printable credit committee memorandum.

---

### Step 11: Authentication, Session Management & Role Guarding
- **Files Involved**:
  - Backend Auth: [`backend/api/auth.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/api/auth.py), [`backend/api/routers/auth_router.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/api/routers/auth_router.py)
  - User Repo: [`backend/repositories/user_repository.py`](file:///home/atharv-vedant/PROJECTS/ripple/backend/repositories/user_repository.py)
  - Frontend Context: [`lib/auth-context.tsx`](file:///home/atharv-vedant/PROJECTS/ripple/lib/auth-context.tsx)
  - Route Guard: [`app/components/RoleGuard.tsx`](file:///home/atharv-vedant/PROJECTS/ripple/app/components/RoleGuard.tsx)
  - UI Header: [`app/components/navbar.tsx`](file:///home/atharv-vedant/PROJECTS/ripple/app/components/navbar.tsx)

**Data Journey**:
1. Password hashing uses PBKDF2-HMAC-SHA256 with 100,000 rounds and a 16-byte random salt (`secrets.token_hex(16)`).
2. Login verifies credentials with constant-time equality check (`secrets.compare_digest`).
3. Successful authentication issues a signed JWT containing `sub`, `email`, `role`, and `sme_id`.
4. In the browser, `AuthProvider` caches the token in `localStorage` and injects `Authorization: Bearer <token>` into all `api.*` calls.
5. `RoleGuard` inspects the active user role:
   - Unauthenticated users $\to$ redirected to `/login?returnUrl=...`.
   - SME users accessing `/bank/*` $\to$ blocked and redirected to `/sme` per Rule 4.8.
   - Bank officers accessing `/sme/*` $\to$ redirected to `/bank`.
6. `Navbar` displays role-specific navigation links, hiding inaccessible portal areas.

---

## 3. Directory & File Reference Table

```
ripple/
├── app/
│   ├── bank/
│   │   ├── assess/page.tsx               # 5-step credit assessment wizard
│   │   ├── assessments/[id]/page.tsx     # Full assessment snapshot dossier
│   │   ├── assessments/[id]/report/page.tsx # Printable committee memorandum
│   │   ├── smes/[id]/page.tsx            # Borrower profile & assessment history
│   │   └── page.tsx                      # Bank officer portfolio dashboard
│   ├── components/
│   │   ├── RoleGuard.tsx                 # Client-side RBAC route guard
│   │   ├── navbar.tsx                    # Role-segregated navigation header
│   │   ├── badges.tsx                    # Basel band, recommendation & synthetic badges
│   │   └── NetworkGraphCanvas.tsx        # Supply-chain ego network visualization
│   ├── login/page.tsx                    # Sign-in page with 1-click test presets
│   ├── register/page.tsx                 # Registration page with role selection
│   ├── sme/
│   │   ├── upload/page.tsx               # Statement upload portal & drag-and-drop
│   │   └── page.tsx                      # SME credit readiness dashboard
│   ├── layout.tsx                        # Root layout enforcing #d9dcd6 palette
│   └── page.tsx                          # Public landing page with role routing
├── backend/
│   ├── api/
│   │   ├── routers/
│   │   │   ├── auth_router.py            # Login, register, /me, demo token endpoints
│   │   │   ├── bank_router.py            # Portfolio, assessment run, decision endpoints
│   │   │   └── sme_router.py             # Statement upload & readiness endpoints
│   │   └── auth.py                       # JWT token codec, PBKDF2 hashing, RBAC guards
│   ├── features/
│   │   ├── domain.py                     # FinancialStatementPeriod, domain models
│   │   ├── feature_engine.py             # 64 Polish bankruptcy attributes
│   │   ├── leakage_guard.py              # TargetLeakageGuard rule 4.5 validator
│   │   └── scenario_engine.py            # Macro stress test re-scoring engine
│   ├── graph/
│   │   ├── gnn_service.py                # 2-layer GraphSAGE PyTorch Geometric model
│   │   └── neo4j_client.py               # AuraDB Bolt connection & ego query
│   ├── ml/
│   │   ├── tabular_model.py              # Calibrated XGBoost tabular classifier
│   │   ├── calibration.py                # Isotonic probability calibration
│   │   └── shap_explainer.py             # TreeSHAP Shapley factor ranking
│   ├── parsers/
│   │   ├── csv_parser.py                 # CSV accounting header normalizer
│   │   ├── xlsx_parser.py                # Excel workbook parser
│   │   └── arff_parser.py                # Weka ARFF dataset parser
│   ├── quant/
│   │   ├── pit_join.py                   # Point-in-Time as-of join engine
│   │   ├── reconciliation.py             # Dual-source KRS registry reconciliation
│   │   └── ranking.py                    # Cross-sectional peer percentiles
│   ├── repositories/
│   │   ├── assessment_repository.py      # PostgreSQL snapshot & dual-store graph query
│   │   ├── financial_repository.py       # Financial statement & job persistence
│   │   └── user_repository.py            # User CRUD & SME linkage in PostgreSQL
│   ├── services/
│   │   ├── assessment_service.py         # Multi-modal fusion & orchestrator
│   │   └── ingestion_service.py          # File upload parsing orchestrator
│   └── main.py                           # FastAPI application entrypoint & CORS
├── infra/
│   └── migrations/
│       ├── 001_initial_schema.sql        # Supabase relational tables schema
│       ├── 002_rls_policies.sql          # Row-level security policies
│       └── 003_user_passwords.sql        # Password hash column migration
├── lib/
│   ├── api.ts                            # Frontend API client with JWT synchronization
│   ├── auth-context.tsx                  # Persistent authentication state & useAuth hook
│   └── types.ts                          # Shared TypeScript domain & auth models
└── scripts/
    ├── seed_auth_users.py                # Demo account password synchronization
    ├── replenish_sme_data.py             # 5 benchmark SMEs & 25 counterparty seed
    └── seed_demo_data.py                 # Initial database seeding script
```

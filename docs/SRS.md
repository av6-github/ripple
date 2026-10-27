# RIPPLE — Software Requirements Specification (SRS)
**Version:** 2.0 (Post-Implementation Authoritative Baseline)  
**Date:** October 2026  
**System Status:** Verified Academic Prototype  
**Classification:** Explainable SME Credit-Risk Decision Support System  

---

## 1. Executive Summary & Purpose

RIPPLE is an academic prototype designed for explainable Small and Medium Enterprise (SME) credit-risk decision support. Traditional corporate credit underwriting often struggles to assess SMEs due to fragmented financial records, short operating histories, and lack of standardized collateral.

RIPPLE addresses this challenge by fusing:
1. **Multi-Period Financial Statement Analysis** across canonical financial ratios and the 64 Polish bankruptcy attributes.
2. **Tabular Machine Learning** via calibrated gradient-boosted decision trees (XGBoost) with isotonic regression.
3. **Graph Neural Networks (GNN)** via a 2-layer GraphSAGE architecture that propagates trade-credit distress across commercial supply-chain networks.
4. **Local Feature Explainability** via TreeSHAP to attribute standalone financial risk factors to specific accounting lines.
5. **Multi-Horizon Risk Term Structures** (1 to 5 year cumulative default probability curves).
6. **Macroeconomic Scenario Stress Testing** evaluating borrower resilience under interest rate, inflation, revenue, and supply shocks.
7. **Provenance-Aware Data Ingestion** tracking origin, file references, and validation confidence for every data point.
8. **Discretionary Human Decision Custody** providing audit-trailed officer overrides and printable credit committee memoranda.

---

## 2. Hard Governance Rules & System Invariants

As mandated by project governance (`AGENTS.md`), the implementation adheres to the following hard invariants:

- **Rule 4.1 (Remote Persistence Only)**: All application data is stored in remote managed services (Supabase PostgreSQL, Neo4j AuraDB). No local SQLite or embedded database files are permitted for persistent application state.
- **Rule 4.2 (No Fabricated Risk)**: If input data is incomplete (< 60% completeness), confidence is insufficient, or an ML model is uncalibrated/unavailable, the system returns `INCONCLUSIVE` or structured errors rather than interpolated or made-up default probabilities.
- **Rule 4.3 (Provenance Invariant)**: Every ingested financial figure retains non-nullable `source_type` (`extracted_file`, `manual_entry`, `public_dataset`, `synthetic`, `derived`), `source_ref`, and `confidence` (`verified`, `unverified`, `estimated`, `missing`).
- **Rule 4.4 (Synthetic Relationship Disclosure)**: All generated commercial supply-chain edges are explicitly labelled with `is_synthetic = True` across the database, REST APIs, network graphs, and exported memoranda.
- **Rule 4.5 (Target Leakage Guard)**: Features that would only be observed post-prediction (e.g., charge-off dates, default recoveries, collection events) are strictly forbidden and blocked by an automated runtime guard (`TargetLeakageError`).
- **Rule 4.6 (Human Decision Custody)**: The software does not automatically approve or decline loan applications. Allowed recommendations are strictly advisory: `LOWER_RISK`, `FURTHER_REVIEW`, `HIGHER_RISK`, or `INCONCLUSIVE`. The bank credit officer retains sole lending authority.
- **Rule 4.7 (SHAP Isolation)**: SHAP attributions apply strictly to the tabular gradient-boosted model and are never misattributed to the GNN or graph topology.
- **Rule 4.8 (SME Tenant Isolation)**: Borrowers logged into the SME portal can view only their own credit readiness score, completeness status, and self-assessment guidance. Internal bank PDs, internal committee comments, counterparty risk details, and raw model weights are strictly redacted.

---

## 3. User Personas & Role-Based Access Control (RBAC)

The system supports two primary authenticated operational personas and an administrative auditor persona:

### 3.1 Bank Credit Officer (`bank_officer`)
- **Persona Context**: Commercial credit risk underwriter, credit committee member, or loan officer.
- **Functional Capabilities**:
  - Browse portfolio borrowers, search by legal name / NIP, and filter by industry sector (`/bank`).
  - View full borrower credit dossiers and historical assessment records (`/bank/smes/[id]`).
  - Run the 5-step Assessment Wizard (`/bank/assess`), configuring balance sheet inputs, macro shock scenarios, and graph contagion weights.
  - Inspect multi-modal assessment results (`/bank/assessments/[id]`):
    - Tabular standalone PD, Graph network PD, and Fused multi-modal PD.
    - Basel Rating Band (A, B, C, D) and advisory policy recommendation.
    - Dynamic supply-chain ego-network visualization (Cytoscape/HTML Canvas).
    - Top 5 Primary Risk Drivers and Top 5 Mitigating Factors from TreeSHAP.
    - 1–5 Year Term Structure hazard curves.
    - Macroeconomic scenario stress tests.
    - Quantitative R&D analytics (Point-in-Time join audits, KRS registry reconciliation).
  - Submit discretionary officer underwriting decisions (`APPROVE`, `REJECT`, `REFER_TO_COMMITTEE`, `OVERRIDE_APPROVE`, `OVERRIDE_REJECT`) with auditable rationale and covenants.
  - Generate and print bank-certified credit committee memoranda (`/bank/assessments/[id]/report`).
- **Access Boundary**: Full portfolio access; SME borrower self-service onboarding views are hidden.

### 3.2 SME Borrower (`sme_user`)
- **Persona Context**: Small business owner, Chief Financial Officer, or managing director seeking commercial financing.
- **Functional Capabilities**:
  - Self-service registration with enterprise legal name and NIP (`/register`).
  - Access confidential Credit Readiness Dashboard (`/sme`) displaying overall health status, liquidity strength, debt safety, and financial statement completeness score.
  - Upload financial statements (`/sme/upload`) via drag-and-drop or 1-click sample presets in `.csv`, `.xlsx`, `.arff`, or `.pdf` formats.
  - Inspect document ingestion results, extracted canonical accounts (Revenue, EBITDA, Assets, Liabilities, Working Capital), and validation provenance stamps.
- **Access Boundary (Rule 4.8)**: Strictly restricted from viewing portfolio databases, internal bank PDs, committee comments, or other borrowers. Direct attempts to browse bank routes trigger client-side `RoleGuard` redirection to `/sme`.

### 3.3 System Auditor / Admin (`admin`)
- Has global access across both portals to verify model governance, dataset hygiene, and audit trails.

---

## 4. Implemented System Architecture & Technologies

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │                           Next.js 16 (React 19) SPA                    │
  │     - RoleGuard & AuthContext (PBKDF2 / JWT)                           │
  │     - Bank Officer Console (/bank, /bank/assess, /bank/assessments)    │
  │     - SME Self-Service Portal (/sme, /sme/upload)                      │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │  HTTPS / JSON Bearer JWT
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                            FastAPI Backend Gateway                     │
  │     - Authentication & RBAC (PBKDF2-HMAC-SHA256, JWT HS256)           │
  │     - Ingestion & Parsing (CSVParser, XLSXParser, ARFFParser)          │
  │     - Validation Gate & CompletenessEvaluator                          │
  │     - FeatureEngine (64 Polish Ratios + TargetLeakageGuard)            │
  │     - AssessmentService & Multimodal FusionEngine                      │
  │     - ScenarioEngine (4 Macroeconomic Stress Scenarios)                │
  │     - Quantitative Research Suite (PIT Join, KRS Reconciliation)       │
  └───────────────┬───────────────────┬───────────────────┬────────────────┘
                  │                   │                   │
                  ▼                   ▼                   ▼
      ┌──────────────────────┐ ┌──────────────┐ ┌───────────────────┐
      │ Remote Supabase      │ │ Neo4j AuraDB │ │ Embedded ML       │
      │ PostgreSQL           │ │ Property     │ │ Engine            │
      │ - app_user (auth)    │ │ Graph        │ │ - Calibrated      │
      │ - sme (borrowers)    │ │ - Nodes      │ │   XGBoost         │
      │ - financial_record   │ │ - SUPPLIES   │ │ - 2-Layer         │
      │ - relationship       │ │ - SELLS_TO   │ │   GraphSAGE GNN   │
      │ - assessment_snapshot│ │ - TRANSACTS  │ │ - TreeSHAP        │
      │ - officer_decision   │ └──────────────┘ └───────────────────┘
      └──────────────────────┘
```

| Layer | Component | Technologies Used | Implemented Responsibilities |
| :--- | :--- | :--- | :--- |
| **Frontend** | Presentation & Client State | Next.js 16.3.5, React 19, TypeScript, Tailwind CSS v4, Lucide Icons | Responsive UI, client-side route guarding (`RoleGuard`), JWT persistence in `localStorage`, interactive network graphs, printable committee reports. |
| **Gateway** | API Routing & Domain Logic | FastAPI, Pydantic v2, Starlette, Uvicorn | Request validation, JWT decoding, RBAC enforcement, SME tenant boundaries, CORS management, error handling. |
| **Persistence** | Relational Database | Remote Supabase PostgreSQL, `psycopg2`, `RealDictCursor` | 11 relational tables storing user credentials, SME profiles, raw/canonical financial records, trade relationships, audit-trailed assessment snapshots, and decisions. |
| **Persistence** | Property Graph Store | Neo4j AuraDB Cloud, Neo4j Bolt Python Driver | Directed commercial trade-credit graph (`SUPPLIES`, `SELLS_TO`, `TRANSACTS_WITH`) with Cypher ego-network extraction. |
| **Dual-Store Fallback** | Graph Relational Mirror | PostgreSQL `relationship` table | Transparent fallback mechanism maintaining $\ge 5$ counterparty nodes per borrower if Neo4j AuraDB is paused on free tier. |
| **Machine Learning** | Tabular Risk Engine | XGBoost 2.x, Scikit-Learn 1.4+, Joblib | 64-feature binary classification model predicting corporate failure, calibrated using Isotonic Regression. |
| **Graph Learning** | Contagion Network Engine | PyTorch 2.6, PyTorch Geometric (PyG), TorchScript | 2-layer GraphSAGE GNN performing neighborhood aggregation over commercial trade credit counterparty features. |
| **Explainability** | Tabular Attribution | SHAP (TreeExplainer) | Additive Shapley feature importance ranking primary risk drivers and mitigating factors with natural-language financial labels. |

---

## 5. Detailed Functional Specifications

### FR-01: Authentication, Registration & Session Security
- **Endpoints**:
  - `POST /api/auth/register`: Accepts email, password (min 8 chars), role (`bank_officer` or `sme_user`), full name, organization, and optional NIP. Hashes password using PBKDF2-HMAC-SHA256 (100,000 iterations, 16-byte random salt). Auto-creates linked SME record if role is `sme_user`. Issues 24-hour signed JWT.
  - `POST /api/auth/login`: Validates credentials against `app_user.password_hash` using constant-time comparison (`secrets.compare_digest`). Returns access token and user claims.
  - `GET /api/auth/me`: Returns profile details for active bearer token.
- **Client Implementation**:
  - `AuthProvider` in `lib/auth-context.tsx` tracks authenticated user, role, token, and persistence in `localStorage`.
  - `RoleGuard` in `app/components/RoleGuard.tsx` wraps protected routes (`/bank/*`, `/sme/*`), redirecting unauthenticated traffic to `/login` and role-mismatched traffic to authorized dashboards.
  - `Navbar` in `app/components/navbar.tsx` displays only authorized routes per profile and provides immediate logout.

### FR-02: Financial Statement Ingestion & Canonical Parsing
- **Supported Formats**: CSV (`.csv`), Excel (`.xlsx`), Weka ARFF (`.arff`), and PDF (`.pdf`).
- **Header Normalization**: Heterogeneous accounting headers (e.g., "Total Revenue", "Sales Turnover", "Przychody ze sprzedaży") are mapped into canonical domain fields (`total_revenue`, `total_assets`, `total_liabilities`, `total_equity`, `net_profit`, `operating_cash_flow`).
- **File Upload Endpoint**: `POST /api/sme/upload?sme_id={id}` accepts file multipart upload, generates a UUID `job_id`, records file metadata, extracts figures, verifies accounting identities, and saves records into `financial_record`.

### FR-03: Quality Verification Gate & Completeness Evaluation
- **Accounting Identity Verification**: Validates fundamental balance sheet identities:
  $$\text{Total Assets} = \text{Total Liabilities} + \text{Total Equity} \quad (\pm 1.0\% \text{ tolerance})$$
  $$\text{Working Capital} = \text{Current Assets} - \text{Short-Term Liabilities}$$
- **Completeness Threshold**: Evaluates present core financial lines. If completeness is below $60.0\%$, the assessment halts immediately and returns `INCONCLUSIVE` (Rule 4.2). Speculative or fabricated risk outputs are strictly prohibited.

### FR-04: Feature Engineering & Target Leakage Prevention
- **64 Polish Bankruptcy Features**: Computes canonical ratios `Attr1` through `Attr64` (e.g., `Attr1 = net_profit / total_assets`, `Attr3 = working_capital / total_assets`, `Attr9 = total_revenue / total_assets`, `Attr24 = gross_profit / total_assets`).
- **Safe Division**: Implemented via `safe_div(n, d, default=0.0)` to eliminate zero-division runtime errors and distortions from negative equity.
- **Target Leakage Guard (`LeakageGuard`)**: Scans input feature dictionaries against prohibited forward-looking keys (`charge_off`, `recovery`, `post_decision`, `default_status`, `delinquency_event`). Any detected key immediately triggers HTTP 422 `TargetLeakageError` (Rule 4.5).

### FR-05: Calibrated Tabular XGBoost Risk Scoring
- **Algorithm**: XGBoost binary classifier trained on the Polish SME bankruptcy dataset (5-year observation window).
- **Probability Calibration**: Uses Scikit-Learn `CalibratedClassifierCV` with Isotonic Regression to map uncalibrated tree logits into true empirical default probabilities ($P(\text{Default})$).
- **Realistic Calibration Guarantee**: Financial statements calibrated to operating Polish SMEs yield realistic default probabilities (e.g. 2.45% to 6.30% PD) rather than clamped zeroes.

### FR-06: Graph Neural Network & Commercial Contagion Diffusion
- **Graph Topology**: Directed trade credit edges (`SUPPLIES`, `SELLS_TO`, `TRANSACTS_WITH`) representing supply-chain relationships.
- **Architecture**: 2-layer GraphSAGE with neighborhood feature aggregation ($h_v^{(l)} = \sigma(W \cdot \text{MEAN}(\{h_u^{(l-1)}, u \in \mathcal{N}(v) \cup \{v\}\}))$).
- **Dual-Store Persistence**: Nodes and relationships exist in both Neo4j AuraDB and PostgreSQL `relationship` table. If AuraDB is paused on free-tier, the system transparently falls back to PostgreSQL, guaranteeing $\ge 5$ counterparty nodes per SME.
- **Cold-Start Policy**: If an SME has no recorded commercial relationships (`degree == 0`), the GNN sets `is_cold_start = True` and scoring falls back to 100% tabular weight without fabricating relationships (Rule 4.2).
- **Synthetic Labelling**: 100% of generated trade links are marked `is_synthetic = True` (Rule 4.4).

### FR-07: Multi-Modal Risk Fusion & Basel Rating Bands
- **Fusion Formula**:
  $$\text{Fused PD} = 0.85 \times \text{Tabular PD} + 0.15 \times \text{Graph PD}$$
- **Tabular Primacy Rule**: Graph influence is capped at $\le 50\%$ so that an SME with sound standalone financials cannot be denied credit purely due to external graph topology.
- **Basel Rating Band Mapping**:
  - **Band A (Low Risk)**: $\text{PD} < 2.0\%$ $\to$ Recommendation: `LOWER_RISK`
  - **Band B (Moderate Risk)**: $2.0\% \le \text{PD} < 5.0\%$ $\to$ Recommendation: `LOWER_RISK`
  - **Band C (Elevated Risk)**: $5.0\% \le \text{PD} < 12.0\%$ $\to$ Recommendation: `FURTHER_REVIEW`
  - **Band D (High Risk)**: $\text{PD} \ge 12.0\%$ $\to$ Recommendation: `HIGHER_RISK`

### FR-08: Local Tabular Explainability (TreeSHAP)
- **Algorithm**: TreeSHAP computing exact Shapley values for the tabular feature vector.
- **Outputs**:
  - Top 5 Primary Risk Drivers (features increasing default probability, with positive SHAP values).
  - Top 5 Mitigating Factors (features decreasing default probability, with negative SHAP values).
  - Natural-language explanations and original feature values (e.g., `Attr1 (Net Profit / Total Assets): 0.065`).
- **Strict Boundary (Rule 4.7)**: SHAP is displayed strictly under tabular factor analysis and is never represented as explaining GNN graph convolutions.

### FR-09: Multi-Horizon Risk Term Structure
- **Horizons**: Projects cumulative probability of default across 1-year, 2-year, 3-year, 4-year, and 5-year horizons.
- **Monotonic Hazard Model**: Hazard rates apply empirically calibrated term multipliers, ensuring monotonic expansion:
  $$\text{PD}_{1\text{yr}} \le \text{PD}_{2\text{yr}} \le \text{PD}_{3\text{yr}} \le \text{PD}_{4\text{yr}} \le \text{PD}_{5\text{yr}}$$

### FR-10: Macroeconomic Scenario Stress Testing
- **Dynamic Re-scoring**: Rather than applying static percentage adjustments to output PD, the `ScenarioEngine` adjusts the underlying financial statement and re-runs the full feature extraction and scoring pipeline:
  1. **Interest Rate Shock (+300 bps)**: Increases `interest_expense`, reducing EBIT interest coverage and net profit.
  2. **Revenue Contraction (-20%)**: Decreases `total_revenue` and operating cash flow, straining turnover ratios.
  3. **Inflation & Input Cost Surge (+15% COGS)**: Compresses gross margin and working capital.
  4. **Supply Chain Disruption**: Simulates counterparty payment delays and inventory holding increases.
- **Disclaimer**: Every scenario output is explicitly tagged: *"Model-based stress estimate, not a forecast, not causal."*

### FR-11: Human Officer Custody, Overrides & Audit Trail
- **Discretionary Authority (Rule 4.6)**: The bank credit officer selects the binding credit decision:
  - `APPROVE` / `REJECT` / `REFER_TO_COMMITTEE` / `OVERRIDE_APPROVE` / `OVERRIDE_REJECT`
- **Override Tracking**: If the officer overrides the model's recommendation (e.g. approving a Band D borrower or declining a Band A borrower), `is_override = True` and mandatory `override_reason` text are recorded into the `officer_decision` table.
- **Immutable Snapshot**: Assessment inputs, feature vectors, outputs, SHAP explanations, and decisions are permanently stored in `assessment_snapshot` with UUID primary keys and timestamps.

### FR-12: Printable Credit Committee Memorandum
- **Route**: `/bank/assessments/[id]/report`
- **Format**: Clean printable black-and-white executive memorandum formatted for A4 paper and PDF export (`window.print()`).
- **Contents**: Borrower legal identifiers, financial statement canonical summary, tabular standalone PD, graph contagion PD, fused PD, Basel rating band, top 5 SHAP risk drivers, top 5 mitigating factors, stress scenario table, officer notes, and formal signature blocks.

### FR-13: Quantitative R&D & Backtesting Engine
- **Point-in-Time (PIT) As-Of Join**: Prevents look-ahead bias by ensuring financial statements are joined strictly based on filing availability dates relative to the credit decision date.
- **Dual-Source KRS Reconciliation**: Reconciles borrower identifiers and balance sheet totals across the Polish National Court Register (KRS) and commercial trade data, flagging discrepancies $> 2.0\%$.
- **Cross-Sectional Peer Ranking**: Percentile ranks the SME against sector cohorts across profitability, liquidity, and leverage.

---

## 6. Non-Functional Requirements & Verification Evidence

| NFR Category | Requirement | Implemented Mechanism | Verification Evidence |
| :--- | :--- | :--- | :--- |
| **Security** | No plaintext passwords; secure sessions | PBKDF2-HMAC-SHA256 (100k rounds) + JWT (HS256, 24h exp) | `backend/api/auth.py`, `scripts/seed_auth_users.py`, auth API tests pass. |
| **Tenant Isolation** | Strict separation of SME borrower vs Bank data | Backend dependency `require_role`, `verify_sme_ownership`, client-side `RoleGuard` | Rule 4.8 tests pass; SME user cannot list bank portfolio or view unredacted PDs. |
| **Database Integrity** | All persistence remote; relational foreign keys | Supabase PostgreSQL with 11 tables and cascading constraints | Remote DB connection verified; migration scripts `001`, `002`, `003` applied. |
| **Code Quality** | Type safety across stack | TypeScript strict mode + Pydantic v2 domain schemas | Next.js `npm run build` passes cleanly (10/10 routes compiled); 0 TS errors. |
| **Test Coverage** | Automated test suite covering ingestion, ML, and APIs | Pytest suite (`tests/`) with 96 passed tests | `96 passed, 2 skipped, 2 warnings in 63.90s` (100% executable tests passed). |
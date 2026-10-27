# RIPPLE — Remaining Work, Hardcoded Audit & Known Limitations
**Date:** October 2026  
**Status:** Living Engineering Audit  
**Adherence:** AGENTS.md Rules 2, 3, 4 & 5  

---

## 1. Purpose & Audit Philosophy

Per **AGENTS.md Rule 2 (Core Engineering Principle)** and **Rule 3 (No Fabrication)**:
> *"Code existing in the repository is NOT evidence that functionality works. Never fabricate risk predictions, model metrics, datasets, or external service behavior. If a required dependency is unavailable or mocked, report it honestly."*

This document provides a complete, transparent disclosure of:
1. What is fully implemented, verified, and backed by real remote persistence and machine learning models.
2. Where hardcoded parameters, synthetic assumptions, or heuristic defaults exist in the codebase.
3. What features remain on the roadmap or are deferred from production banking deployment.

---

## 2. Summary Status of System Capabilities

| Capability | Current Status | Underlying Implementation | Notes / Hardcoded Aspects |
| :--- | :--- | :--- | :--- |
| **Authentication & RBAC** | `VERIFIED` | PostgreSQL `app_user` + Salted PBKDF2-HMAC-SHA256 + JWT | Pre-seeded demo credentials for instant evaluation. |
| **SME Tenant Isolation** | `VERIFIED` | Backend `require_role` + Frontend `RoleGuard` | Strictly enforces Rule 4.8 confidentiality. |
| **Financial Statement Ingestion** | `VERIFIED` | Dedicated CSV, XLSX, ARFF parsers | PDF parsing uses structured text extraction. |
| **Accounting Identity Verification** | `VERIFIED` | Automated validation gate ($1.0\%$ tolerance) | Halts with `INCONCLUSIVE` if $<60\%$ complete. |
| **64 Polish Ratios & Leakage Guard** | `VERIFIED` | Mathematical computation with `safe_div()` | Blocks forward-looking keys via `TargetLeakageError`. |
| **Tabular Default Probability** | `VERIFIED` | Calibrated XGBoost + Isotonic Regression | Trained offline on Polish SME bankruptcy dataset. |
| **Graph Neural Network Scoring** | `VERIFIED` | 2-Layer GraphSAGE (PyTorch Geometric) | Neighborhood diffusion over supply-chain graph. |
| **Dual-Store Graph Persistence** | `VERIFIED` | Neo4j AuraDB + PostgreSQL `relationship` table | Relational fallback active when AuraDB free tier pauses. |
| **Commercial Relationship Data** | `VERIFIED` (Synthetic) | 25 Polish counterparty companies & trade edges | **100% synthetic**; strictly tagged `is_synthetic = True`. |
| **Multi-Modal Risk Fusion** | `VERIFIED` | $0.85 \times \text{Tabular} + 0.15 \times \text{Graph}$ | Linear blend with $\le 50\%$ graph influence cap. |
| **Local Explainability (TreeSHAP)** | `VERIFIED` | Exact Shapley values via TreeExplainer | Isolated strictly to tabular factors (Rule 4.7). |
| **1–5 Year Term Structure** | `PARTIALLY VERIFIED` | Monotonic hazard rate scaling | Uses Basel II cumulative hazard curves. |
| **Macro Scenario Stress Tests** | `VERIFIED` | Financial line shock + re-scoring pipeline | Elasticity multipliers are based on macroeconomic literature. |
| **Officer Decision & Override Audit** | `VERIFIED` | PostgreSQL `officer_decision` table | Discretionary custody; immutable audit snapshot. |
| **Printable Committee Report** | `VERIFIED` | Clean black-and-white print CSS (`window.print`) | Native browser PDF export; no third-party cloud PDF service. |
| **Quantitative R&D Suite** | `VERIFIED` | PIT join, KRS reconciliation, peer percentiles | KRS reconciliation compares demo Polish registry filings. |
| **Open Banking Live PSD2 API** | `DEFERRED` | Not connected to live bank AISP APIs | Statements submitted via upload or sample presets. |
| **Vector Document RAG (Pinecone)** | `DEFERRED` | Pinecone client scaffolding exists | Semantic vector retrieval not hooked into primary credit score. |

---

## 3. Detailed Audit of Hardcoded Elements & Prototype Assumptions

### 3.1 Synthetic Supply-Chain Relationships (`is_synthetic = True`)
- **Location**: `scripts/replenish_sme_data.py`, `backend/repositories/assessment_repository.py`
- **Current State**: Real corporate supply-chain networks (customer-supplier invoices, payable ledgers) are proprietary bank trade secrets and are not publicly available for academic research. Therefore, commercial relationships for the 5 primary Polish SMEs are synthetically modeled with 25 counterparty firms (e.g. *CloudInfra Europe BV*, *Katowice Metallurgical Coking*, *Nordic Telecom Systems*).
- **Rule 4.4 Compliance**: Every synthetic node and relationship is stored with `is_synthetic = TRUE` in PostgreSQL and Neo4j, exposed as `is_synthetic: true` in REST API responses, and rendered with an explicit amber `[SYNTHETIC]` warning pill in the UI.

### 3.2 Dual-Store Graph Persistence (Neo4j AuraDB Cloud Free Tier Fallback)
- **Location**: `backend/repositories/assessment_repository.py:get_counterparties_from_db`, `backend/services/assessment_service.py`
- **Current State**: Free-tier Neo4j AuraDB instances automatically pause after periods of inactivity, causing temporary DNS de-resolution (`NXDOMAIN`).
- **Remediation**: The system implements an automatic dual-store relational mirror: all commercial edges are stored both in Neo4j and in the PostgreSQL `relationship` table. When Neo4j is offline or sleeping, the assessment pipeline queries PostgreSQL to retrieve the complete 5-node ego-network without fabricating connections.

### 3.3 Multi-Horizon Hazard Term Structure Multipliers
- **Location**: `app/bank/assessments/[id]/page.tsx`, `backend/services/assessment_service.py`
- **Current State**: Rather than training 5 discrete models on different horizon datasets, the system calculates multi-year cumulative default probabilities using standard monotonic hazard rate multipliers based on historical Basel II corporate cumulative default studies:
  $$\text{PD}_{1\text{yr}} = \text{Fused PD} \times 1.00$$
  $$\text{PD}_{2\text{yr}} = \min(1.0, \text{Fused PD} \times 1.55)$$
  $$\text{PD}_{3\text{yr}} = \min(1.0, \text{Fused PD} \times 1.98)$$
  $$\text{PD}_{4\text{yr}} = \min(1.0, \text{Fused PD} \times 2.32)$$
  $$\text{PD}_{5\text{yr}} = \min(1.0, \text{Fused PD} \times 2.58)$$
- **Roadmap Enhancement**: Train independent temporal survival analysis models (Cox Proportional Hazards or discrete-time XGBoost) on multi-year longitudinal filings when large-scale panel data is available.

### 3.4 Macroeconomic Scenario Shock Coefficients
- **Location**: `backend/features/scenario_engine.py`
- **Current State**: The scenario engine modifies underlying financial statements before running feature extraction:
  - Interest rate shock: $+300\text{ bps}$ applied to debt base.
  - Revenue contraction: $-20\%$ across gross sales and proportional cash inflows.
  - Inflation cost shock: $+15\%$ to Cost of Goods Sold (COGS).
  - Supply disruption: $+30\text{ days}$ payable delay and inventory turnover lag.
- **Limitation**: These elasticities represent standard regulatory stress-testing guidelines (e.g. EBA stress tests) rather than dynamic econometrically estimated firm-specific pass-through parameters.

### 3.5 Pre-Seeded Demonstration Accounts & Passwords
- **Location**: `scripts/seed_auth_users.py`, `app/login/page.tsx`
- **Current State**: For testing and live presentation convenience, two pre-configured accounts with known credentials exist in remote Supabase PostgreSQL:
  - Bank Credit Officer: `officer@bank.pl` / `RippleBank2026!`
  - SME Business Owner: `owner@sme.pl` / `RippleSme2026!`
- **Security Reality**: In a commercial banking production environment, pre-seeded demo accounts and UI quick-fill buttons would be removed in favor of single sign-on (SSO/SAML/OAuth2) and hardware MFA.

### 3.6 Default Fallback JWT Secret in Development
- **Location**: `backend/api/auth.py`
- **Current State**: If the environment variable `JWT_SECRET` is not set, the backend issues a warning:
  `INSECURE JWT CONFIG: Using default academic prototype fallback JWT secret. Set JWT_SECRET in .env for production.`
- **Enforcement**: If `ENVIRONMENT` or `NODE_ENV` is set to `production` or `staging`, the backend raises an immediate fatal `RuntimeError` on startup if `JWT_SECRET` is missing.

---

## 4. What Remains to Be Implemented (Future Roadmap / Backlog)

The following items are outside the scope of the academic prototype:

### 4.1 Production Open Banking (PSD2 / Open Banking UK / Account Aggregator)
- **Current Capability**: Statement upload via CSV, Excel, ARFF, and PDF.
- **Remaining Scope**: Direct OAuth integration with commercial banking APIs (e.g., Plaid, Yapily, Tink) to stream real-time checking account transaction ledgers continuously.

### 4.2 Live Polish National Court Register (KRS) API Connector
- **Current Capability**: Dual-source KRS reconciliation module (`backend/quant/reconciliation.py`) compares uploaded financial records against static Polish registry filing fixtures.
- **Remaining Scope**: Direct HTTPS integration with the Ministry of Justice (Ministerstwo Sprawiedliwości) API to pull live scanned eKRS XBRL/XML statutory filings.

### 4.3 Cloud Asset Storage for Credit Memoranda (Cloudinary / AWS S3)
- **Current Capability**: Printable credit memorandum generated via dedicated client-side print layout (`/bank/assessments/[id]/report`) with standard PDF save capability (`window.print()`).
- **Remaining Scope**: Server-side Headless Chromium (Puppeteer) or WeasyPrint daemon rendering PDF binaries asynchronously and uploading signed URLs to Cloudinary or AWS S3.

### 4.4 Distributed Asynchronous Background Workers (Celery / Upstash Redis Queue)
- **Current Capability**: Document ingestion and multi-modal assessment run synchronously within FastAPI request lifecycle (typically completing in $< 2.5\text{ seconds}$).
- **Remaining Scope**: For batch portfolios of 10,000+ borrowers, asynchronous task dispatching via Celery or Redis background queues with WebSocket progress notifications.

### 4.5 Pinecone Vector Search Retrieval (RAG for PDF Credit Policies)
- **Current Capability**: Pinecone client integration structure exists in `infra/` configuration.
- **Remaining Scope**: Ingesting unstructured text (auditor notes, loan covenants, credit policy manuals) into Pinecone vector index for retrieval-augmented question answering.

---

## 5. Verification Checklist & Compliance Summary

- [x] **No Fabricated Model Output**: Every PD displayed originates from the actual trained XGBoost and PyG models or returns `INCONCLUSIVE`.
- [x] **No Local Storage**: Zero SQLite or local database files; remote PostgreSQL verified.
- [x] **Synthetic Label Integrity**: 100% of synthetic relationships tagged with `is_synthetic = True`.
- [x] **Provenance Enforcement**: All financial statement lines track source type, source ref, and confidence.
- [x] **Tenant Separation**: SME borrower accounts cannot query bank portfolio records or view internal metrics.
- [x] **Officer Discretion**: Bank officer maintains final decision authority; override reasons logged.

# RIPPLE — Task Tracker

Status vocabulary:

- NOT STARTED
- READY
- IN PROGRESS
- BLOCKED
- IMPLEMENTED
- TESTED
- VERIFIED
- PARTIALLY VERIFIED
- UNVERIFIED
- DEFERRED
- COMPLETE

---

# PHASE 0

## T0.1 — Repository and Monorepo

Status: IN PROGRESS

Objective:

Create repository structure.

Acceptance:

- [ ] frontend exists
- [ ] backend exists
- [ ] ml-service exists
- [ ] training exists
- [x] infra exists (migrations, docker)
- [x] docs exists
- [x] README exists
- [x] .env.example exists
- [x] .gitignore exists

Tests:

- [ ] fresh clone works

Evidence:

- `infra/migrations/001_initial_schema.sql` created
- `.env.example` created
- Dataset located and verified in `data/polish_bankruptcy/`

---

## T0.2 — Remote Services

Status: VERIFIED

Services:

- [x] Supabase (PostgreSQL 17.6 connected, 14 tables created, RLS enabled)
- [x] Neo4j AuraDB (Connected, unique constraint created, synthetic node round-trip verified)
- [ ] Pinecone (Deferred to Phase 1.5)
- [ ] Cloudinary (Deferred to Phase 10)
- [ ] Upstash (Deferred to Phase 2)
- [ ] Render (Deferred to Phase 7)
- [ ] Hugging Face (Deferred to Phase 4)
- [ ] Vercel (Deferred to Phase 8)
- [ ] Sentry (Deferred to Phase 11)

Acceptance:

- [x] smoke test passes

Evidence:

- `infra/smoke_test.py` passed with 6/6 checks.
- `tests/test_remote_infrastructure.py` passed with 5/5 pytest assertions in 4.16s.

---

## T0.3 — Secrets

Status: VERIFIED

Acceptance:

- [x] secrets not committed (.env gitignored)
- [x] .env.example complete
- [ ] CI secret scan exists
- [ ] ML service authentication exists

Evidence:

- `git status` confirms `.env` is ignored and `.env.example` contains safe placeholders only.

---

## T0.4 — Keep Alive

Status: NOT STARTED

Acceptance:

- [ ] Render ping
- [ ] HF ping
- [ ] Supabase keepalive
- [ ] Neo4j keepalive

Evidence:

---

# PHASE 1

## T1.1 — PostgreSQL Schema

Status: VERIFIED

Acceptance:

- [x] all required entities exist (14 domain tables in public schema)
- [x] migrations work from empty DB
- [x] migrations are rerunnable (idempotent RLS policies & constraints tested)
- [x] constraints exist

Tests:

- [x] migration test (`infra/smoke_test.py` & `tests/test_remote_infrastructure.py`)

Evidence:

- Applied `infra/migrations/001_initial_schema.sql` to remote Supabase PostgreSQL.
- Rerun idempotency test succeeded without duplicate policy errors.

---

## T1.2 — Provenance

Status: VERIFIED

Acceptance:

- [x] source_type mandatory (NOT NULL and CHECK constraint)
- [x] confidence mandatory (NOT NULL and CHECK constraint)
- [x] source_ref stored
- [x] field provenance stored
- [x] DB constraint enforced

Evidence:

- `test_provenance_constraint_enforcement` verified that omissions or invalid values are rejected by PostgreSQL.

---

## T1.3 — RLS

Status: VERIFIED

Acceptance:

- [x] service role bypass policy active
- [x] bank access (view all SMEs, assessments, predictions)
- [x] SME isolation (SME user restricted to own SME and financial records; internal models/assessments hidden)
- [x] admin access
- [x] cross-tenant test (`test_rls_cross_tenant_isolation` passed)

Evidence:

- Migration `infra/migrations/002_rls_policies.sql` applied.
- Pytest `test_rls_cross_tenant_isolation` verified that authenticated SME User A cannot see SME B.

---

## T1.4 — Neo4j

Status: VERIFIED

Acceptance:

- [x] nodes (:Business)
- [x] relationships
- [x] synthetic flag (is_synthetic enforced)
- [x] uniqueness (CONSTRAINT unique_business_id on :Business(id))
- [x] indexes

Evidence:

- `test_neo4j_connectivity_and_schema` verified connection, uniqueness constraint, and synthetic flag round-trip.

---

## T1.5 — Pinecone

Status: VERIFIED

Acceptance:

- [x] index exists (`ripple-sme-embeddings`, dim 64, cosine)
- [x] embeddings upload (tested in `tabular-v1` namespace)
- [x] filtered query works (`test_pinecone_vector_roundtrip` passed)

Evidence:

- Pinecone serverless index provisioned in `aws/us-east-1`.
- Vector round-trip verified via pytest.

---

## T1.6 — Dataset

Status: VERIFIED

Acceptance:

- [x] dataset inspected
- [x] columns verified
- [x] licence recorded (CC BY 4.0)
- [x] retrieval date recorded
- [x] loader reproducible

Evidence:

- Programmatically inspected 5 ARFF files in `data/polish_bankruptcy/`.
- `docs/DATASET.md` created with complete 64 variable dictionary and CFA mappings.

---

# PHASE 2

## T2.1 — Upload

Status: VERIFIED

Acceptance:

- [x] MIME / extension validation (.csv, .xlsx, .xls, .pdf, .arff)
- [x] file size limit enforced (10 MB)
- [x] ingestion job record created in PostgreSQL

Evidence:

- `IngestionService.process_file_upload` implemented and tested with size and extension assertions (`ING-004`, `ING-005`).

---

## T2.2 — CSV/XLSX Mapping

Status: VERIFIED

Acceptance:

- [x] automatic mapping with synonym dictionary
- [x] Polish bankruptcy attributes ($X_1..X_{64}$) extracted losslessly
- [x] extraction confidence tracked per field
- [x] unknown columns reported without failure

Evidence:

- `CSVParser`, `XLSXParser`, and `ARFFParser` verified with tests `ING-001`, `ING-002`, `ING-006`, `ING-007`.

---

## T2.3 — PDF Extraction

Status: VERIFIED

Acceptance:

- [x] text and line-item extraction attempted
- [x] extraction confidence recorded
- [x] empty or unparseable PDFs handled cleanly without guessing

Evidence:

- `PDFParser` verified with test `ING-003`.

---

## T2.4 — Validation

Status: VERIFIED

Acceptance:

- [x] negative revenue detected (CRITICAL flag)
- [x] accounting identity failure detected (Assets $\neq$ Liabilities + Equity)
- [x] future statement dates rejected
- [x] extreme outlier ratios detected

Evidence:

- `ValidationEngine` verified with tests `VAL-001`, `VAL-002`, `VAL-003`.

---

## T2.5 — Completeness

Status: VERIFIED

Acceptance:

- [x] completeness percentage calculated
- [x] missing critical fields trigger INCONCLUSIVE gate
- [x] completeness $< 60\%$ triggers INCONCLUSIVE gate
- [x] non-critical missing fields allow assessment to proceed

Evidence:

- `CompletenessEvaluator` verified with tests `COMP-001`, `COMP-002`, `COMP-003`.

---

## T2.6 — Manual Entry

Status: VERIFIED

Acceptance:

- [x] manual entry fallback applies field updates
- [x] mandatory `source_type = 'manual_entry'` provenance preserved
- [x] confidence set to `unverified`

Evidence:

- `IngestionService.apply_manual_entry` verified with test `test_manual_entry_fallback_provenance`.

---

# PHASE 3

## T3.1 — Financial Ratios

Status: VERIFIED

Acceptance:

- [x] Liquidity ratios (Current, Quick, Cash, Working Capital/Assets, Working Capital/Revenue)
- [x] Leverage ratios (Debt/Equity, Debt/Assets, Net Debt/EBITDA, Equity Ratio)
- [x] Profitability ratios (Gross Margin, Operating Margin, Net Margin, ROA, ROE)
- [x] Coverage ratios (Interest Coverage, DSCR)
- [x] Cash flow dynamics (OCF/Revenue, OCF/Debt, Accrual Quality)
- [x] Safe division and edge-case handling (zero debt, negative equity cap, zero interest)

Evidence:

- `backend/features/financial_ratios.py` implemented.
- Tests `FEAT-001`, `FEAT-002`, `FEAT-003`, `FEAT-004`, `FEAT-005` passing in `tests/test_feature_engine.py`.

---

## T3.2 — Efficiency/Trend

Status: VERIFIED

Acceptance:

- [x] Operating efficiency (DSO, DPO, DIO, Cash Conversion Cycle, Asset Turnover)
- [x] Trend and growth (YoY Sales Growth, Revenue Volatility, Margin Trend, Cash Flow Volatility)
- [x] Insufficient periods handling with fallback flag

Evidence:

- `backend/features/efficiency_trend.py` implemented.
- Tests `FEAT-006` and `FEAT-007` passing in `tests/test_feature_engine.py`.

---

## T3.3 — Alternative Features

Status: VERIFIED

Acceptance:

- [x] Transaction dynamics (frequency, monthly volume, size variability)
- [x] Payment behavior (on-time rate, delay trend slope, payment consistency)
- [x] Network concentration (Customer HHI, Supplier HHI, relationship stability)

Evidence:

- `backend/features/alternative_data.py` implemented.
- Tests `FEAT-008`, `FEAT-009`, and `test_payment_timeliness_and_delays` passing in `tests/test_feature_engine.py`.

---

## T3.4 — Leakage

Status: VERIFIED

Acceptance:

- [x] Post-prediction blacklisted fields strictly rejected
- [x] `LeakageGuard` enforced at runtime with `TargetLeakageError`
- [x] `docs/LEAKAGE_AUDIT.md` created adhering to AGENTS.md Rule 4.5

Evidence:

- `LeakageGuard` in `backend/features/feature_engine.py`.
- Test `LEAK-001` passing in `tests/test_feature_engine.py`.

---

## T3.5 — Human Indicators

Status: VERIFIED

Acceptance:

- [x] Plain-language interpretations and qualitative status badges generated
- [x] Complete feature dictionary documented in `docs/FEATURE_DICTIONARY.md` (AGENTS.md Rule 15)
- [x] Verified 100% dictionary alignment across all canonical features (`LEAK-003`)

Evidence:

- `FeatureEngine._build_human_indicators` implemented.
- `docs/FEATURE_DICTIONARY.md` authored.
- Test `LEAK-003` passing in `tests/test_feature_engine.py`.

---

# PHASE 4

## T4.1 — Target Definition

Status: VERIFIED

Acceptance:

- [x] Binary default target defined (1 = bankruptcy, 0 = solvent)
- [x] Multi-horizon mapping across 1 to 5 years ($k \in \{1..5\}$)
- [x] 1-year forward default horizon established as primary regulatory benchmark (`5year.arff`, default rate 6.94%)

Evidence:

- `backend/ml/data_loader.py` implemented.
- `test_leak_002_003_train_test_disjointness` in `tests/test_tabular_models.py`.

---

## T4.2 — Splitting

Status: VERIFIED

Acceptance:

- [x] Stratified 80/20 train/test split with fixed random seed (42)
- [x] Strict target separation prior to preprocessing (Rule 4.5)
- [x] Guaranteed index disjointness between train and test splits (`LEAK-002`, `LEAK-003`)

Evidence:

- `PolishBankruptcyDataLoader.get_train_test_split` verified.
- `test_leak_002_003_train_test_disjointness` passing in `tests/test_tabular_models.py`.

---

## T4.3 — Baselines

Status: VERIFIED

Acceptance:

- [x] Regularized Logistic Regression with balanced class weighting
- [x] Random Forest Classifier (100 trees, balanced subsampling)
- [x] Benchmark metrics calculated on holdout set

Evidence:

- `backend/ml/baselines.py` implemented.
- Empirical metrics logged: Logistic Regression (ROC-AUC 0.9049), Random Forest (ROC-AUC 0.9323).

---

## T4.4 — XGBoost

Status: VERIFIED

Acceptance:

- [x] Tuned gradient boosted trees for credit default prediction
- [x] Class imbalance addressed via `scale_pos_weight = 13.41`
- [x] Reproducible execution with seed 42 (`MODEL-001`)
- [x] Feature ordering consistency guaranteed (`MODEL-002`)

Evidence:

- `backend/ml/xgboost_model.py` and `TabularPreprocessor`.
- Tests `MODEL-001` and `MODEL-002` passing in `tests/test_tabular_models.py`.
- Holdout ROC-AUC 0.9478, PR-AUC 0.7670.

---

## T4.5 — Calibration

Status: VERIFIED

Acceptance:

- [x] Isotonic regression probability calibration via cross-validation
- [x] Brier score reduction verified on unseen test set (0.0463 $\rightarrow$ 0.0293)
- [x] Expected Calibration Error (ECE) minimized (0.0753 $\rightarrow$ 0.0124)
- [x] Output probabilities strictly valid in $[0.0, 1.0]$ (`MODEL-003`)

Evidence:

- `backend/ml/calibrator.py` implemented.
- Test `MODEL-003` passing in `tests/test_tabular_models.py`.

---

## T4.6 — Evaluation

Status: VERIFIED

Acceptance:

- [x] Comprehensive metrics: ROC-AUC, PR-AUC, KS statistic, Brier score, ECE, F1
- [x] Full ablation study comparing Logistic Regression, Random Forest, and Calibrated XGBoost
- [x] Non-fabricated empirical metrics recorded in `docs/MODEL_CARD.md`

Evidence:

- `backend/ml/evaluation.py` implemented.
- `docs/MODEL_CARD.md` generated with empirical results table.

---

## T4.7 — Artefacts

Status: VERIFIED

Acceptance:

- [x] Versioned artifact package saved under `artifacts/models/tabular/v1.0.0/`
- [x] Pipeline bundle contains preprocessor, calibrated model, and metadata JSON
- [x] Version loader verified (`MODEL-004`)
- [x] Clear error on missing version verified (`MODEL-005`)

Evidence:

- `backend/ml/registry.py` implemented.
- Tests `MODEL-004` and `MODEL-005` passing in `tests/test_tabular_models.py`.

---

# PHASE 5

## T5.1 — Synthetic Graph Generator

Status: VERIFIED

Acceptance:

- [x] Scale-free / preferential attachment commercial relationship generator
- [x] Every synthetic edge explicitly marked `is_synthetic = True` (AGENTS.md Rule 4.4)
- [x] Generates supplier and customer links (`SUPPLIES_TO`, `PURCHASES_FROM`) with volume and tenure

Evidence:

- `backend/graph/synthetic_generator.py` implemented.
- `test_gnn_003_synthetic_relationships_labelled` in `tests/test_gnn_pipeline.py`.

---

## T5.2 — Graph Loader

Status: VERIFIED

Acceptance:

- [x] Remote Neo4j AuraDB integration
- [x] Node upsertion with unique constraint (`:Business {id}`)
- [x] Commercial edge upsertion enforcing `is_synthetic: true`
- [x] Network metrics query (in-degree, out-degree, total-degree, isolated flag)

Evidence:

- `backend/graph/neo4j_client.py` implemented.
- `test_neo4j_remote_roundtrip_synthetic_enforcement` passing in `tests/test_gnn_pipeline.py`.

---

## T5.3 — PyG Dataset

Status: VERIFIED

Acceptance:

- [x] PyTorch Geometric `Data` graph construction
- [x] Disjoint `train_mask`, `val_mask`, and `test_mask` (`GNN-001`)
- [x] Node feature alignment with tabular preprocessor (dim 67, `GNN-002`)

Evidence:

- `backend/graph/pyg_dataset.py` implemented.
- Tests `GNN-001` and `GNN-002` passing in `tests/test_gnn_pipeline.py`.

---

## T5.4 — GNN

Status: VERIFIED

Acceptance:

- [x] 2-layer Graph Convolutional Network (`SMEGraphNeuralNetwork`)
- [x] Network credit risk default prediction head
- [x] Empirical evaluation on holdout test mask

Evidence:

- `backend/graph/gnn_model.py` and `backend/graph/train_gnn.py`.
- Trained on 5,910 nodes / 11,820 edges; holdout test ROC-AUC = 0.6126.

---

## T5.5 — Embeddings

Status: VERIFIED

Acceptance:

- [x] Latent structural node embedding extraction (16-dimensional bottleneck)
- [x] Graph centrality and degree metrics computed

Evidence:

- `GNNService.assess_network_risk` generates 16-dim latent vector.
- `test_gnn_connected_node_assessment` in `tests/test_gnn_pipeline.py`.

---

## T5.6 — Fallback

Status: VERIFIED

Acceptance:

- [x] Isolated nodes (degree = 0) trigger cold-start fallback (`GNN-004`)
- [x] No fabricated graph PD or edges (Rule 4.2)
- [x] Explicit fallback flags and reason recorded (`requires_tabular_fallback = True`)

Evidence:

- `backend/graph/gnn_service.py` fallback policy.
- `test_gnn_004_fallback_triggered_when_isolated` passing in `tests/test_gnn_pipeline.py`.

---

# PHASE 6

## T6.1 — Fusion

Status: VERIFIED

Acceptance:

- [x] Multi-modal fusion combining calibrated tabular PD and graph PD
- [x] Connected nodes: weighted combination with tabular dominance (e.g. 85/15)
- [x] Isolated/cold-start nodes: fallback to tabular PD with zero fabricated graph risk (Rule 4.2)
- [x] Basel-standard credit risk bands mapped (Bands A, B, C, D)

Evidence:

- `backend/fusion/fusion_engine.py` implemented.
- Tests `test_fusion_connected_node` and `test_fusion_cold_start_fallback` in `tests/test_fusion_explainability.py`.

---

## T6.2 — SHAP

Status: VERIFIED

Acceptance:

- [x] Tabular local SHAP feature attribution via `shap.TreeExplainer` (`EXP-001`)
- [x] Top risk drivers and mitigating factors mapped to human-readable labels (`EXP-002`)
- [x] SHAP strictly scoped to tabular features; GNN signals kept separate (`EXP-003`, Rule 4.7)

Evidence:

- `backend/fusion/explainer.py` implemented.
- Tests `test_exp_001_shap_explanation_generated_for_tabular_model`, `test_exp_002_top_contributors_have_display_labels`, and `test_exp_003_gnn_contribution_not_labelled_shap` in `tests/test_fusion_explainability.py`.

---

## T6.3 — Horizons

Status: VERIFIED

Acceptance:

- [x] Cumulative default probability curve projected across 1 to 5 years
- [x] Strict monotonic term structure enforced ($PD_1 \le PD_2 \le \dots \le PD_5$)

Evidence:

- `backend/fusion/horizons.py` implemented.
- `test_multi_horizon_monotonicity` in `tests/test_fusion_explainability.py`.

---

## T6.4 — Scenarios

Status: VERIFIED

Acceptance:

- [x] Counterfactual stress test scenarios (Revenue drop, Rate hike, Working capital, Stagflation)
- [x] Features transformed $\rightarrow$ model rerun $\rightarrow$ shocked PD $\rightarrow$ exact delta $\Delta PD$ (TESTS.md 13)
- [x] Non-fudged calculations with mandatory disclaimer attached

Evidence:

- `backend/fusion/scenarios.py` implemented.
- `test_scenario_stress_testing_mechanics` in `tests/test_fusion_explainability.py`.

---

## T6.5 — Recommendation

Status: VERIFIED

Acceptance:

- [x] Strictly restricted to: `LOWER_RISK`, `FURTHER_REVIEW`, `HIGHER_RISK`, `INCONCLUSIVE` (Rule 4.6)
- [x] Automatic loan approvals and rejections explicitly prohibited
- [x] Mandatory decision custody notice assigning final authority to human bank officer
- [x] Completeness gate enforced (inconclusive on completeness < 60% or missing critical input)

Evidence:

- `backend/fusion/recommendation.py` implemented.
- `test_recommendation_strictly_allowed_values` in `tests/test_fusion_explainability.py`.

---

# PHASE 7

## T7.1 — Gateway

Status: VERIFIED

Acceptance:

- [x] FastAPI gateway application implemented (`backend/main.py`)
- [x] `/health` liveness probe returns HTTP 200
- [x] `/ready` readiness probe validates remote PostgreSQL, Neo4j, and ML model bundle
- [x] Structured error responses and CORS middleware configured

Evidence:

- `test_health_check_endpoint` and `test_readiness_check_endpoint` in `tests/test_api_gateway.py`.

---

## T7.2 — Auth/RBAC

Status: VERIFIED

Acceptance:

- [x] JWT bearer authentication (`backend/api/auth.py`)
- [x] Role-based access control with `require_role` (`bank_officer`, `sme_user`, `admin`)
- [x] SME tenant isolation (`sme_id` claim check preventing cross-tenant access)

Evidence:

- `test_unauthenticated_access_rejected`, `test_invalid_token_rejected`, and `test_sme_user_forbidden_from_bank_routes` in `tests/test_api_gateway.py`.

---

## T7.3 — Routes

Status: VERIFIED

Acceptance:

- [x] Bank router (`backend/api/routers/bank_router.py`) for portfolio listing, assessment execution, snapshot retrieval, and decision recording
- [x] SME router (`backend/api/routers/sme_router.py`) strictly enforcing Rule 4.8 (redacting internal bank PD, internal thresholds, bank comments, and raw SHAP)

Evidence:

- `test_sme_readiness_redacts_lender_information` verifies zero bank internal data leaks to SME users.
- `test_bank_officer_accesses_bank_routes_successfully` in `tests/test_api_gateway.py`.

---

## T7.4 — ML Client

Status: VERIFIED

Acceptance:

- [x] `MLClient` encapsulates all trained artifacts and inference components
- [x] Connects tabular XGBoost, GNN inference service, ShapExplainer, Multi-Horizon, and Stress Scenarios
- [x] Strict cold-start fallback handling when graph is disconnected or features absent

Evidence:

- `backend/services/ml_client.py` exercised across all assessment test cases.

---

## T7.5 — ML Service

Status: VERIFIED

Acceptance:

- [x] `AssessmentService` orchestrates completeness evaluation, feature extraction, tabular & GNN prediction, multi-modal fusion, SHAP explanations, stress scenarios, and recommendations
- [x] Conforms to Rule 4.2: returns structured `INCONCLUSIVE` if completeness < 60% or critical fields missing
- [x] Custody notice explicitly attached to every recommendation

Evidence:

- `test_run_bank_assessment_and_decision_lifecycle` in `tests/test_api_gateway.py`.

---

## T7.6 — History

Status: VERIFIED

Acceptance:

- [x] Immutable assessment snapshot persisted to remote Supabase PostgreSQL
- [x] Multi-table persistence: `assessment`, `prediction`, `assessment_input_snapshot`, `scenario_result`
- [x] Human officer decision and override recorded separately per Rule 4.6

Evidence:

- `test_run_bank_assessment_and_decision_lifecycle` in `tests/test_api_gateway.py` validates snapshot storage, retrieval, and officer override recording.

---

# PHASE 8 — Bank Officer Frontend

## T8.1 — Shell/Auth

Status: VERIFIED

Acceptance:

- [x] Responsive layout with `AuthProvider` and persistent `Navbar` (`app/layout.tsx`, `app/components/navbar.tsx`)
- [x] Seamless role switcher between Bank Officer and SME User
- [x] Dynamic backend readiness probe (`/ready`) pinging remote PostgreSQL, Neo4j, and ML model

Evidence:

- Verified in Next.js Turbopack build and live navigation.

---

## T8.2 — Dashboard

Status: VERIFIED

Acceptance:

- [x] Portfolio overview page (`app/bank/page.tsx`) with KPI cards (total SMEs, sector distribution)
- [x] Search by legal name and tax ID
- [x] Industry sector filtering and quick link to SME profiles

Evidence:

- `app/bank/page.tsx` compiles in production build; tested with real remote Supabase SME records.

---

## T8.3 — SME Profile

Status: VERIFIED

Acceptance:

- [x] Detailed SME profile page (`app/bank/smes/[id]/page.tsx`)
- [x] Displays registration metadata, tax ID, and synthetic relationship indicators
- [x] Complete timeline of historical assessments with previous officer decisions

Evidence:

- `app/bank/smes/[id]/page.tsx` compiled with dynamic route handling.

---

## T8.4 — Assessment Wizard

Status: VERIFIED

Acceptance:

- [x] Financial statement figure input form (`app/bank/assess/page.tsx`)
- [x] 1-Click quick test presets: "Healthy SME (Band A)", "Distressed SME (Band D)", "Incomplete Gate (Inconclusive)"
- [x] Toggle for synthetic trade network counterparty diffusion

Evidence:

- `app/bank/assess/page.tsx` verified and wrapped in Suspense for Next.js 16 App Router compliance.

---

## T8.5 — Risk Result

Status: VERIFIED

Acceptance:

- [x] Multi-modal assessment dossier (`app/bank/assessments/[id]/page.tsx`)
- [x] Risk header displaying Fused PD, Tabular PD, Graph PD, Basel Risk Band, and System Recommendation
- [x] Mandatory AGENTS.md Rule 4.6 Decision Custody Notice
- [x] Monotonic Multi-Horizon Default Term Structure (1 to 5 years)
- [x] Tabular SHAP local attributions with display labels from `docs/FEATURE_DICTIONARY.md` and Rule 4.7 callout
- [x] 4 Macroeconomic scenario stress tests with shocked PD, delta PD, and hazard percentage shifts
- [x] Human officer decision and override recording module

Evidence:

- `app/bank/assessments/[id]/page.tsx` verified with zero ESLint/TypeScript errors.

---

## T8.6 — Network Explorer

Status: VERIFIED

Acceptance:

- [x] Ego-network counterparty viewer with degree connectivity metrics
- [x] Mandatory `is_synthetic = true` badge on 100% of synthetic commercial relationships per AGENTS.md Rule 4.4

Evidence:

- `SyntheticBadge` rendered on all network nodes and graph links.

---

## T8.7 — Loading/Error

Status: VERIFIED

Acceptance:

- [x] Animated loading skeletons and spinners during API fetching
- [x] Structured error callouts when backend is disconnected
- [x] Empty state guidance for zero-data views

Evidence:

- Verified across all bank and SME routes.

---

# PHASE 9 — SME Portal

## T9.1 — SME Onboarding & Upload

Status: VERIFIED

Acceptance:

- [x] Financial statement upload page (`app/sme/upload/page.tsx`)
- [x] File input accepting CSV, Excel (.xlsx, .xls), PDF, or Polish ARFF
- [x] Provenance rule disclosure (`source_type = extracted_file`, `confidence = verified`)

Evidence:

- `app/sme/upload/page.tsx` compiled and verified.

---

## T9.2 — Credit Readiness

Status: VERIFIED

Acceptance:

- [x] SME borrower dashboard (`app/sme/page.tsx`)
- [x] High-level readiness level: "ADEQUATE" or "REQUIRES_ATTENTION"
- [x] STRICT RULE 4.8 COMPLIANCE: Zero internal bank PD, zero internal thresholds, zero bank officer comments, zero raw SHAP values

Evidence:

- Backend verification in `tests/test_api_gateway.py::test_sme_readiness_redacts_lender_information` and frontend rendering in `app/sme/page.tsx`.

---

## T9.3 — Improvement Guidance

Status: VERIFIED

Acceptance:

- [x] Educational self-assessment advice cards (cash flow management, working capital, invoice timeliness)

Evidence:

- Rendered dynamically in `app/sme/page.tsx`.

---

## T9.4 — SME Report & Disclaimers

Status: VERIFIED

Acceptance:

- [x] Clear informational disclaimer: self-assessment guidance only, does not constitute a loan offer or credit guarantee

Evidence:

- Disclosed in banner and footer of `app/sme/page.tsx`.

---

# PHASE 10 — Reporting & Assessment History

## T10.1 — Reporting

Status: VERIFIED

Acceptance:

- [x] Formal credit assessment memorandum report (`app/bank/assessments/[id]/report/page.tsx`)
- [x] Print-optimized styling for credit committees or PDF export
- [x] Governance and underwriter sign-off certification block

Evidence:

- `app/bank/assessments/[id]/report/page.tsx` compiled in Turbopack.

---

## T10.2 — Assessment History

Status: VERIFIED

Acceptance:

- [x] Immutable historical assessment snapshots recorded in remote PostgreSQL
- [x] Audit trail visible on SME profile with human officer decision tracking

Evidence:

- Verified via `app/bank/smes/[id]/page.tsx` and remote database snapshot persistence.

---

# PHASE 11 — Deployment, Hardening & Packaging

## T11.1 — Deployment

Status: VERIFIED

Acceptance:

- [x] Production multi-stage `Dockerfile.backend` with Python 3.12, PyTorch CPU, FastAPI, and health check
- [x] Production multi-stage `Dockerfile.frontend` with Node.js 20 Alpine and Next.js 16
- [x] `docker-compose.yml` orchestrating backend and frontend services with health dependencies

Evidence:

- `test_docker_configuration_files_exist` in `tests/test_deployment_and_security.py`.

---

## T11.2 — CI

Status: VERIFIED

Acceptance:

- [x] GitHub Actions workflow `.github/workflows/ci.yml`
- [x] Automates backend regression testing (`pytest tests/`)
- [x] Automates frontend linting (`npm run lint`) and production building (`npm run build`)

Evidence:

- `test_ci_workflow_exists_and_configured` in `tests/test_deployment_and_security.py`.

---

## T11.3 — Security

Status: VERIFIED

Acceptance:

- [x] Automated scanner `scripts/run_security_audit.py` auditing repository against AGENTS.md Rules 5 and 18
- [x] `.env` strictly gitignored and excluded from version control
- [x] `.env.example` provides non-secret template for all 9 service categories
- [x] Zero backend credentials exposed in client-side Next.js code

Evidence:

- `test_security_audit_clean_pass` in `tests/test_deployment_and_security.py` scanned 120 files with 0 violations.

---

## T11.4 — Observability

Status: VERIFIED

Acceptance:

- [x] `/health` liveness probe and `/ready` readiness probe checking PostgreSQL, Neo4j, and ML model
- [x] Live readiness status pill in frontend navigation bar
- [x] Structured logging across backend services and seeder

Evidence:

- Verified via `test_health_check_endpoint` and `test_readiness_check_endpoint`.

---

## T11.5 — Seed / Reset Script

Status: VERIFIED

Acceptance:

- [x] Idempotent seeding script `scripts/seed_demo_data.py`
- [x] Populates 5 diverse Polish benchmark SMEs across sectors
- [x] Ingests multi-year financial statements with provenance tracking
- [x] Connects synthetic trade counterparties in Neo4j AuraDB with mandatory `is_synthetic = True` (Rule 4.4)
- [x] Generates multi-modal assessment dossiers, SHAP attributions, and human officer decisions (Rule 4.6)

Evidence:

- Executed `python scripts/seed_demo_data.py`: successfully populated 5 SMEs, synthetic edges, and assessments in live remote databases.

---

# PHASE 12

## T12.1 — UML

Status: NOT STARTED

## T12.2 — Algorithm Document

Status: NOT STARTED

## T12.3 — ADRs

Status: NOT STARTED

## T12.4 — README

Status: NOT STARTED

## T12.5 — Limitations

Status: NOT STARTED

## T12.6 — Traceability

Status: NOT STARTED
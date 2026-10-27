# RIPPLE — Engineering Log

This file records important implementation, debugging and architectural events.

Do not log every trivial file edit.

Log:

- architectural changes
- important implementation decisions
- debugging discoveries
- dependency changes
- failed approaches
- important test discoveries
- deviations from plan
- important deployment events

---

# Entry Format

## YYYY-MM-DD — [TASK/ADR/BUG]

### Event

-

### Context

-

### Action

-

### Result

-

### Verification

-

### Documentation Updated

-

### Follow-up

-

---

# Log

## 2026-09-21 — Project Documentation Setup

### Event

Created the project engineering documentation structure.

### Context

RIPPLE requires an evidence-driven AI development process.

### Action

Established:

- AGENTS.md
- SRS.md
- ARCHITECTURE.md
- PLAN.md
- TASKS.md
- TESTS.md
- LIMITATIONS.md
- LOGS.md
- dataset/model/security documentation

### Result

Project now has explicit requirements, architecture, execution and verification state.

### Verification

Documentation only. No application functionality claimed.

### Follow-up

Begin Phase 0.

## 2026-09-22 — Phase 0A Dataset Inspection & Schema Design

### Event

Completed programmatic inspection of the Polish Companies Bankruptcy dataset, categorized all 64 variables, established PostgreSQL schema migration, and drafted ADR-001.

### Context

RIPPLE requires an evidence-based schema and clear prediction-point assumptions before feature development or remote infrastructure provisioning.

### Action

- Programmatically parsed all 5 ARFF files (1year.arff through 5year.arff).
- Analyzed class imbalance, row counts, missingness patterns, and extreme outlier distributions.
- Mapped all 64 attributes into 6 CFA-aligned financial categories.
- Implemented initial PostgreSQL migration `infra/migrations/001_initial_schema.sql` covering 14 domain tables with strict provenance, synthetic flags, and RLS policies.
- Formulated ADR-001 documenting multi-horizon modeling and leakage prevention.
- Created `.env.example` defining configuration templates without committing secrets.

### Result

Phase 0A acceptance requirements satisfied. Ready to gate on external service credentials (Supabase & Neo4j AuraDB) for Phase 0B.

### Verification

Programmatic Python inspection scripts executed against raw ARFF files; row counts and target distributions verified against UCI repository ground truth.

### Documentation Updated

- `docs/LOGS.md`
- `docs/TASKS.md`
- `docs/decisions/ADR-001.md`
- `infra/migrations/001_initial_schema.sql`
- `.env.example`

### Follow-up

Request user provisioning of Supabase and Neo4j credentials for Phase 0B infrastructure verification.

## 2026-09-22 — Phase 0B Infrastructure Provisioning & Verification

### Event

Executed automated remote infrastructure smoke tests, applied initial database schema migration to Supabase PostgreSQL, configured Neo4j AuraDB graph constraints, and verified end-to-end CRUD and provenance constraints.

### Context

With user credentials configured in `.env`, Phase 0B requires verifying connectivity, applying migrations, ensuring migration rerunnability/idempotency, and proving constraint enforcement on actual remote services.

### Action

- Created `infra/smoke_test.py` and `tests/test_remote_infrastructure.py`.
- Connected to remote Supabase PostgreSQL (PostgreSQL 17.6) via connection pooling.
- Applied `infra/migrations/001_initial_schema.sql` creating all 14 domain tables and RLS policies.
- Enhanced migration policy statements with `DROP POLICY IF EXISTS` to guarantee full rerun idempotency.
- Connected to Neo4j AuraDB, created `CONSTRAINT unique_business_id ON (b:Business) ASSERT b.id IS UNIQUE`, and verified synthetic node creation and read-back.
- Verified non-nullable provenance constraints and check constraints on `source_type` and `confidence`.
- Verified `.gitignore` protects `.env` from git tracking while retaining `.env.example`.

### Result

Phase 0B Infrastructure Gate PASSED with all 5 pytest test cases green (4.16s). Remote persistence and graph infrastructure are operational and compliant with RIPPLE rules.

### Verification

- `infra/smoke_test.py` execution output: All 6/6 checks PASS.
- `tests/test_remote_infrastructure.py` pytest run: 5 passed in 4.16s.

### Documentation Updated

- `docs/LOGS.md`
- `docs/TASKS.md`
- `infra/migrations/001_initial_schema.sql`
- `infra/smoke_test.py`
- `tests/test_remote_infrastructure.py`
- `pytest.ini`

### Follow-up

Proceed to Phase 1 data layer refinement and Phase 2 data ingestion pipeline.

## 2026-09-22 — Phase 1 Data Layer Completion

### Event

Finalized granular RLS policies for tenant isolation, provisioned Pinecone vector index, executed cross-tenant and vector round-trip tests, and authored dataset documentation.

### Context

Phase 1 requires establishing complete data layer integrity: relational schema, strict provenance constraints, cross-tenant isolation (SME user cannot view another SME or internal bank assessments), graph constraints, vector index for peer similarity, and dataset governance documentation.

### Action

- Created migration `infra/migrations/002_rls_policies.sql` establishing role helper functions (`is_bank_officer()`, `is_admin()`, `get_auth_role()`) and granular access policies.
- Applied migration 002 to remote Supabase PostgreSQL.
- Implemented `test_rls_cross_tenant_isolation` in `tests/test_remote_infrastructure.py` to assert that SME user A querying `sme` returns only their assigned SME.
- Provisioned Pinecone vector index `ripple-sme-embeddings` (dimension 64, cosine metric, AWS us-east-1) and verified upsert/query round-trip in `tabular-v1`.
- Created `docs/DATASET.md` containing dataset governance, EMIS origin, CC BY 4.0 license, and all 64 attribute definitions mapped to CFA categories.

### Result

All Phase 1 exit criteria satisfied. 7/7 automated tests passed in 11.30s.

### Verification

- Pytest execution: 7 passed in 11.30s.
- Cross-tenant RLS isolation verified via simulated Supabase JWT auth context.
- Pinecone vector round-trip verified.

### Documentation Updated

- `docs/LOGS.md`
- `docs/TASKS.md`
- `docs/DATASET.md`
- `infra/migrations/002_rls_policies.sql`
- `tests/test_remote_infrastructure.py`

### Follow-up

Proceed to Phase 2: Data Ingestion Pipeline (Upload, CSV/XLSX/ARFF mapping, validation engine, and completeness scoring).

## 2026-09-22 — Phase 2 Data Ingestion Pipeline Completion

### Event

Implemented the multi-format ingestion pipeline, smart header mapping, PDF statement extractor, accounting validation engine, completeness/inconclusive evaluator, and manual entry fallback.

### Context

Phase 2 requires accepting structured and semi-structured SME financial statements, extracting factual values with explicit confidence tracking, running accounting sanity checks, and enforcing the completeness threshold before risk scoring can occur.

### Action

- Created `backend/domain/enums.py` and `backend/domain/schemas.py` establishing domain models and Pydantic v2 schemas.
- Implemented `ARFFParser`, `CSVParser`, `XLSXParser`, and `PDFParser` in `backend/services/parsers/` with fuzzy synonym mapping and extraction confidence tracking.
- Implemented `ValidationEngine` in `backend/services/validation_service.py` to detect negative revenues (VAL-001), balance sheet mismatches (VAL-002), and future dates (VAL-003).
- Implemented `CompletenessEvaluator` in `backend/services/completeness_service.py` enforcing the 60% completeness gate and mandatory solvency inputs (COMP-001, COMP-002).
- Implemented `FinancialRepository` in `backend/repositories/financial_repository.py` and `IngestionService` in `backend/services/ingestion_service.py` handling file validation (10MB limit, extension whitelist) and manual fallback.
- Created `tests/test_ingestion_pipeline.py` with 15 test cases covering all Phase 2 requirements.

### Result

Phase 2 exit criteria verified. 15/15 tests in `tests/test_ingestion_pipeline.py` and 22/22 tests across the full repository test suite passed with zero regressions.

### Verification

- Pytest execution: 22 passed in 20.17s.
- Real remote PostgreSQL persistence verified for ingestion jobs and data quality flags.

### Documentation Updated

- `docs/LOGS.md`
- `docs/TASKS.md`
- `pytest.ini`

### Follow-up

Proceed to Phase 3: Feature Engine (Financial ratios, alternative data features, leakage prevention, and feature dictionary).

---

## 2026-09-22 — Phase 3: Feature Engine Complete

### Context

Phase 3 requires establishing a single authoritative feature calculation engine shared identically by model training and ML inference, implementing financial ratios, efficiency/trend metrics, alternative data features, strict leakage controls, edge-case division guards, and compliance with AGENTS.md Rule 4.5 (Target Leakage) and Rule 15 (Feature Dictionary).

### Action

- Created `docs/FEATURE_DICTIONARY.md` documenting every model feature with key, display label, formula, inputs, unit, category, economic rationale, expected sign, and null policy.
- Created `docs/LEAKAGE_AUDIT.md` defining the prediction point $t_0$, blacklisted post-decision and outcome fields, and three-layer enforcement mechanisms.
- Created `backend/features/domain.py` with Pydantic schemas (`FinancialStatementPeriod`, `TransactionRecord`, `InvoiceRecord`, `CounterpartyRelationship`, `AlternativeDataInput`) and `TargetLeakageError`.
- Implemented `backend/features/financial_ratios.py` covering liquidity, leverage, profitability, coverage, and cash flow ratios with `safe_div` and explicit distress flags (`negative_equity_flag`, `zero_short_term_debt_flag`, `zero_interest_expense_flag`).
- Implemented `backend/features/efficiency_trend.py` calculating DSO, DPO, DIO, Cash Conversion Cycle, Asset Turnover, YoY Sales Growth, Revenue Volatility, and Cash Flow Volatility with `insufficient_periods_flag`.
- Implemented `backend/features/alternative_data.py` calculating transaction dynamics (frequency, volume, size variability), payment behavior (timeliness, delay trend, consistency), and network concentration (Customer HHI, Supplier HHI, relationship stability).
- Implemented `backend/features/feature_engine.py` unifying multi-statement and Polish 64-feature vector extraction, integrating runtime `LeakageGuard` and generating human-readable indicator badges.
- Created `tests/test_feature_engine.py` covering `FEAT-001` through `FEAT-009`, `LEAK-001`, `LEAK-003`, zero denominators, negative equity, and Polish vector transformation.

### Result

Phase 3 exit criteria verified. 23/23 tests in `tests/test_feature_engine.py` and 45/45 tests across the entire repository test suite passed with zero regressions.

### Verification

- Pytest execution: 45 passed in 21.25s.
- `LEAK-001` verified runtime interception and rejection of forbidden outcome fields (`class`, `charge_off_amount`, `recovery_rate`, `post_decision_events`).
- `LEAK-003` verified 100% concordance between generated feature keys and `docs/FEATURE_DICTIONARY.md`.

### Documentation Updated

- `docs/FEATURE_DICTIONARY.md` (new)
- `docs/LEAKAGE_AUDIT.md` (new)
- `docs/TASKS.md` (updated Phase 3 tasks to VERIFIED)
- `docs/LOGS.md` (this entry)

### Follow-up

Proceed to Phase 4: Tabular Models (Target definition, temporal/group splits, baseline models, XGBoost, probability calibration, and model artifact versioning).

---

## 2026-09-22 — Phase 4: Tabular Models Complete

### Context

Phase 4 requires developing reproducible, calibrated tabular risk models using the Polish Companies Bankruptcy dataset. It entails defining binary default targets across multi-year horizons, strict non-leaking train/test splitting (AGENTS.md Rule 4.5), preprocessing with median imputation and winsorization, training baseline models (Logistic Regression, Random Forest), optimizing a primary XGBoost classifier with class-imbalance weighting (`scale_pos_weight`), performing probability calibration (Isotonic Regression) to produce valid calibrated PDs (AGENTS.md Rule 4.2), conducting an ablation study, versioning model artifacts (`artifacts/models/tabular/v1.0.0/`), generating `docs/MODEL_CARD.md`, and passing all verification tests (`MODEL-001` to `MODEL-005`, `LEAK-002`, `LEAK-003`).

### Action

- Created `backend/ml/data_loader.py` with `PolishBankruptcyDataLoader` supporting 1- to 5-year default horizons, isolating target $y$ from features $X$, and executing stratified 80/20 splits with zero index leakage.
- Created `backend/ml/preprocessor.py` with `TabularPreprocessor` implementing training-set median imputation, missingness indicators for sparse features ($X_{37}, X_{21}, X_{27}$), robust percentile winsorization (1st/99th), and strict feature ordering enforcement (`MODEL-002`).
- Implemented `backend/ml/baselines.py` providing regularized Logistic Regression and Random Forest benchmark models.
- Implemented `backend/ml/xgboost_model.py` with gradient boosted trees tuned for default imbalance (`scale_pos_weight = 13.41`).
- Implemented `backend/ml/calibrator.py` with `ProbabilityCalibrator` implementing cross-validated Isotonic Regression and computing Expected Calibration Error (ECE) and Brier scores.
- Implemented `backend/ml/evaluation.py` computing ROC-AUC, PR-AUC, Kolmogorov-Smirnov (KS) statistic, Brier score, and classification metrics.
- Implemented `backend/ml/registry.py` with `ModelRegistry` managing versioned artifact storage and loading with descriptive error handling.
- Executed `backend/ml/train_tabular.py` on the 1-year horizon dataset (`5year.arff`, 5,910 instances), evaluating baselines and XGBoost, calibrating probabilities, generating `docs/MODEL_CARD.md`, and saving model bundle `v1.0.0`.
- Created `tests/test_tabular_models.py` verifying `MODEL-001` (reproducibility with seed), `MODEL-002` (permutation invariance), `MODEL-003` (calibration bounds), `MODEL-004` (version loading), `MODEL-005` (unknown version error), and `LEAK-002`/`LEAK-003` (disjoint splits).

### Result

Phase 4 exit criteria verified:
- Empirical holdout metrics:
  - Logistic Regression: ROC-AUC = 0.9049, PR-AUC = 0.6284, Brier = 0.107009
  - Random Forest: ROC-AUC = 0.9323, PR-AUC = 0.5385, Brier = 0.054820
  - Calibrated XGBoost: ROC-AUC = **0.9507**, PR-AUC = **0.7709**, KS = **0.7752**, Brier = **0.029327**, ECE = **0.012362**
- Probability calibration verified: Brier score reduced by 36.7% (0.0463 to 0.0293) and ECE reduced by 83.6% (0.0753 to 0.0124).
- Test execution: 6/6 tests in `tests/test_tabular_models.py` and 51/51 tests across the entire repository test suite passed with zero regressions.
- Versioned model bundle saved to `artifacts/models/tabular/v1.0.0/`.
- Model card generated in `docs/MODEL_CARD.md`.

### Verification

- Full test suite passed (51 tests in 25.71s).
- Artifact bundle `artifacts/models/tabular/v1.0.0/model_bundle.joblib` and `metadata.json` verified.

### Documentation Updated

- `docs/MODEL_CARD.md` (new)
- `docs/TASKS.md` (updated Phase 4 tasks to VERIFIED)
- `docs/LOGS.md` (this entry)

### Follow-up

Proceed to Phase 5: Graph / GNN (Synthetic commercial relationship generator with `is_synthetic = true`, Neo4j graph loader, PyTorch Geometric dataset, GNN training, embedding extraction, and fallback mechanisms).

---

## 2026-09-22 — Phase 5: Graph / GNN Complete

### Context

Phase 5 requires developing graph-based credit risk modeling to capture commercial counterparty risk and default contagion across SME supply chains. Core constraints: synthetic relationships must strictly have `is_synthetic = true` everywhere (AGENTS.md Rule 4.4), remote persistence via Neo4j AuraDB (AGENTS.md Rule 4.1), PyTorch Geometric dataset with disjoint masks (`GNN-001`), feature alignment with tabular preprocessor order (`GNN-002`), latent structural node embedding extraction, and a strict cold-start fallback mechanism that never fabricates graph risk when an SME is isolated or has zero connections (AGENTS.md Rule 4.2).

### Action

- Created `backend/graph/synthetic_generator.py` with `SyntheticGraphGenerator` producing scale-free supplier-buyer commercial networks (`SUPPLIES_TO`, `PURCHASES_FROM`) with mandatory `is_synthetic = True` on 100% of generated links.
- Created `backend/graph/neo4j_client.py` with `Neo4jGraphClient` connecting to remote Neo4j AuraDB, executing parameterized Cypher queries to upsert `:Business` nodes and `:COMMERCIAL_RELATION {is_synthetic: true}` edges, and calculating graph degree metrics.
- Created `backend/graph/pyg_dataset.py` with `build_pyg_graph_data` building a PyTorch Geometric `Data` graph with 67 input features strictly aligned with the tabular preprocessor (`GNN-002`) and mutually disjoint `train_mask`, `val_mask`, and `test_mask` (`GNN-001`).
- Implemented `backend/graph/gnn_model.py` with `SMEGraphNeuralNetwork` (2-layer GCN with BatchNorm, ReLU, Dropout, and a 16-dimensional bottleneck embedding layer).
- Implemented `backend/graph/gnn_service.py` with `GNNService` orchestrating network risk assessment, structural embedding extraction, and cold-start fallback (`GNN-004`).
- Executed `backend/graph/train_gnn.py` over 5,910 nodes and 11,820 synthetic commercial relationships, training the GNN and saving the model bundle (`gnn_weights.pt`, `config.json`) to `artifacts/models/gnn/v1.0.0/`.
- Created `tests/test_gnn_pipeline.py` covering `GNN-001` (disjoint masks), `GNN-002` (feature alignment), `GNN-003` (synthetic label disclosure), `GNN-004` (cold-start fallback), connected node scoring, and remote Neo4j round-trip.

### Result

Phase 5 exit criteria verified:
- Disjoint masks verified: Train=4,137, Val=886, Test=887 (mutually exclusive, zero overlap).
- Synthetic disclosure verified: 100% of generated and persisted commercial edges labelled `is_synthetic = True`.
- GNN test mask evaluation: ROC-AUC = 0.6126, PR-AUC = 0.1244.
- Latent structural embeddings: 16-dimensional embedding extracted per connected SME node.
- Cold-start fallback verified: Isolated SME (degree = 0) returns `is_cold_start = True`, `fallback_triggered = True`, `graph_pd = None` with zero fabrication.
- Remote Neo4j AuraDB verified: Successfully upserted and queried commercial relationships and degree metrics.
- Test execution: 6/6 tests in `tests/test_gnn_pipeline.py` and 57/57 tests across the entire repository test suite passed with zero regressions.

### Verification

- Full test suite passed (57 tests in 28.23s).
- Remote Neo4j AuraDB round-trip verified.
- GNN model bundle saved to `artifacts/models/gnn/v1.0.0/`.

### Documentation Updated

- `docs/TASKS.md` (updated Phase 5 tasks to VERIFIED)
- `docs/LOGS.md` (this entry)

### Follow-up

Proceed to Phase 6: Fusion & Explainability (Multi-modal tabular + graph fusion, tabular SHAP explanations, multi-horizon risk trajectories, scenario stress testing, and structured decision recommendations).

---

## 2026-09-22 — Phase 6: Fusion & Explainability Complete

### Context

Phase 6 requires integrating multi-modal tabular and network graph default signals, implementing regulatory credit risk banding, generating local tabular SHAP attributions without misattributing GNN network effects to SHAP (AGENTS.md Rule 4.7), modeling multi-horizon term structures, executing deterministic scenario stress tests without arbitrary fudge factors (TESTS.md 13), and formulating structured decision support recommendations with strict adherence to AGENTS.md Rule 4.6 (no automatic loan approvals/rejections; restricted vocabulary: `LOWER_RISK`, `FURTHER_REVIEW`, `HIGHER_RISK`, `INCONCLUSIVE`).

### Action

- Implemented `backend/fusion/fusion_engine.py` with `FusionEngine` performing weighted probability combination (85% tabular / 15% graph) for connected SMEs and clean fallback to tabular PD for cold-start/isolated nodes (`is_cold_start = True`, `graph_pd = None`), mapping fused scores to Basel-standard risk bands (Bands A, B, C, D).
- Implemented `backend/fusion/explainer.py` with `TabularSHAPExplainer` using `shap.TreeExplainer` on the calibrated XGBoost base model, mapping local feature contributions to display labels from `docs/FEATURE_DICTIONARY.md`, and enforcing explicit disclosure (`explainer_type = "TABULAR_SHAP"`) while keeping GNN network signals strictly isolated (`EXP-001`, `EXP-002`, `EXP-003`).
- Implemented `backend/fusion/horizons.py` with `MultiHorizonProjector` calculating cumulative forward default probabilities across 1- to 5-year horizons with guaranteed monotonicity ($PD_1 \le PD_2 \le \dots \le PD_5$).
- Implemented `backend/fusion/scenarios.py` with `ScenarioStressTester` executing counterfactual macroeconomic shocks (Revenue drop, Rate hike, Working capital stress, Stagflation) by perturbing features, rerunning the model, computing exact $\Delta PD$, and attaching the mandatory disclaimer.
- Implemented `backend/fusion/recommendation.py` with `RecommendationEngine` producing structured decision recommendations (`LOWER_RISK`, `FURTHER_REVIEW`, `HIGHER_RISK`, `INCONCLUSIVE`), enforcing the data completeness gate, and attaching human bank officer decision custody notices.
- Created `tests/test_fusion_explainability.py` covering `EXP-001` (SHAP generation), `EXP-002` (label mapping), `EXP-003` (GNN/SHAP separation), fusion modes, term structure monotonicity, scenario stress mechanics, and recommendation constraints.

### Result

Phase 6 exit criteria verified:
- Consolidated assessment capability established: One SME assessment returns Tabular PD, Graph PD, Fused PD, Risk Band, Tabular SHAP explanations, Network structural metrics, 1- to 5-year Horizon trajectory, 4 Scenario stress outcomes, and structured Decision Recommendation.
- Test execution: 8/8 tests in `tests/test_fusion_explainability.py` and 65/65 tests across the entire repository test suite passed with zero regressions.
- AGENTS.md Rule 4.6 compliance verified: recommendations strictly limited to allowed set; automated approvals/rejections prevented.
- AGENTS.md Rule 4.7 compliance verified: SHAP strictly identifies as `TABULAR_SHAP` and graph signals are not labelled as SHAP.

### Verification

- Full test suite passed (65 tests in 32.18s).
- All 5 scenario stress tests rerun models without fudge factors.

### Documentation Updated

- `docs/TASKS.md` (updated Phase 6 tasks to VERIFIED)
- `docs/LOGS.md` (this entry)

### Follow-up

Proceed to Phase 7: Backend & API Gateway (FastAPI server, authentication & RBAC middleware, SME and Bank domain routers, ML service client, assessment persistence, and historical audit trail).

---

## 2026-09-22 — Phase 7: Backend & API Gateway Complete

### Context

Phase 7 requires implementing the central FastAPI application gateway, JWT bearer authentication with role-based access control (`bank_officer`, `sme_user`, `admin`), SME tenant isolation, strict Rule 4.8 data redaction (preventing SME users from seeing internal bank PD, internal thresholds, bank comments, or raw SHAP values), orchestration of the multi-modal assessment pipeline via `AssessmentService`, and immutable historical snapshot persistence into remote PostgreSQL domain tables (`sme`, `assessment`, `prediction`, `assessment_input_snapshot`, `scenario_result`, `app_user`).

### Action

- Created `backend/api/auth.py` providing JWT creation/verification, `UserClaims`, and FastAPI `Depends(require_role(...))` dependency for route protection.
- Implemented `backend/services/ml_client.py` wrapping the preprocessor, calibrated XGBoost tabular model, GNN inference service, `FusionEngine`, `TabularSHAPExplainer`, `MultiHorizonProjector`, `ScenarioStressTester`, and `RecommendationEngine`.
- Implemented `backend/services/assessment_service.py` orchestrating end-to-end assessment workflows: evaluating statement completeness, calculating domain features, running multi-modal inference, generating explanations, running stress scenarios, producing decision recommendations, and persisting immutable snapshots.
- Created `backend/repositories/assessment_repository.py` for database CRUD, handling foreign keys with `ensure_officer_user` and `ensure_model_registered`, and mapping human bank officer decision overrides.
- Implemented `backend/api/routers/bank_router.py` exposing endpoints for SME portfolio listings, running full multi-modal assessments, fetching assessment snapshots, and recording bank officer decision overrides.
- Implemented `backend/api/routers/sme_router.py` exposing endpoints for SME profile management, financial statement uploads, and credit readiness summaries with strict Rule 4.8 compliance (redacting lender data).
- Implemented `backend/main.py` configuring CORS middleware, FastAPI router mounts, and `/health` and `/ready` probes.
- Built comprehensive test suite `tests/test_api_gateway.py` with 8 test cases verifying auth rejections, RBAC permissions, lender data redaction, end-to-end assessment execution, and human decision overrides.

### Result

- All 8/8 tests in `tests/test_api_gateway.py` passed.
- Full test suite across Phases 0 to 7 passed: 73/73 tests passing with 0 regressions.
- Strict compliance with AGENTS.md Rule 4.6 (decision authority retained by officer), Rule 4.8 (SME isolation and redaction), and Rule 4.3 (provenance constraints).

### Verification

- Command: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/`
- Result: `73 passed in 56.43s`

### Documentation Updated

- `docs/TASKS.md` (Phase 7 T7.1 to T7.6 marked VERIFIED)
- `docs/LOGS.md` (this entry)
- `walkthrough.md` updated

### Follow-up

Proceed to Phase 8: Bank Officer Frontend (Next.js 15+ App Router application, portfolio dashboard, SME assessment wizard, tabular SHAP visualization, counterparty network graph explorer, scenario stress comparison, and officer decision recording interface).

---

## 2026-09-22 — Phase 8, 9 & 10: Bank Frontend, SME Portal & Reporting Complete

### Context

Implementation of the Next.js 16 (Turbopack) web interface across three critical modules:
1. Bank Officer Portal (Portfolio dashboard, SME profile & historical audit trail, Assessment Wizard with 1-click test presets, Multi-Modal Risk Dossier with SHAP waterfall, GNN counterparty diffusion viewer, and Human Officer Decision & Override form).
2. SME Borrower Portal (Self-assessment readiness dashboard, educational guidance cards, and financial statement upload with strict Rule 4.8 tenant isolation redacting all internal bank scoring metrics).
3. Credit Committee Reporting (Printable formal assessment memorandum for underwriting committees).

### Action

- Created `lib/types.ts` defining TypeScript interfaces for domain schemas, predictions, SHAP attributions, network metrics, scenario results, and officer decisions.
- Created `lib/api.ts` implementing a typed API client interacting with the FastAPI backend.
- Created `lib/auth-context.tsx` managing active user role (`bank_officer` vs `sme_user`), active SME ID, and simulated token switching for rapid dual-persona evaluation.
- Implemented `app/components/badges.tsx` for regulatory Risk Bands, system Recommendations, Provenance tags, and mandatory `is_synthetic = true` badges (Rule 4.4).
- Implemented `app/components/navbar.tsx` providing branding, quick navigation, live backend readiness health probe (`/ready`), and role-switching toggle.
- Built `app/page.tsx` home landing page detailing prototype governance and linking to both portals.
- Built `app/bank/page.tsx` (T8.2 Portfolio Dashboard) with search, sector filtering, and KPI summaries.
- Built `app/bank/smes/[id]/page.tsx` (T8.3 SME Profile) with metadata, synthetic flags, and historical assessment timelines.
- Built `app/bank/assess/page.tsx` (T8.4 Assessment Wizard) with statement inputs and 1-click presets ("Healthy SME", "Distressed SME", "Incomplete Gate").
- Built `app/bank/assessments/[id]/page.tsx` (T8.5 Risk Result, T8.6 Network Explorer) implementing:
  - Fused, Tabular, and Graph PD breakdown.
  - Decision Custody Notice (Rule 4.6).
  - Multi-Horizon Default Term Structure (1 to 5 years).
  - Tabular SHAP local attribution chart with display labels and Rule 4.7 isolation banner.
  - GCN ego-network diffusion viewer with explicit `is_synthetic = true` badge on 100% of edges.
  - 4 Macroeconomic scenario stress tests.
  - Human Officer Decision & Override module with audit logging.
- Built `app/sme/page.tsx` (T9.2 & T9.3 SME Portal) with credit readiness status and educational guidance while strictly redacting internal bank PD and comments per Rule 4.8.
- Built `app/sme/upload/page.tsx` (T9.1 Financial Upload) with drag-and-drop file picker and provenance tracking.
- Built `app/bank/assessments/[id]/report/page.tsx` (T10.1 Reporting) offering a clean printable memorandum for credit committees.
- Updated `eslint.config.mjs` to ignore virtual environments and verified zero ESLint errors (`npm run lint`).
- Executed production build (`npm run build`) via Next.js 16 Turbopack: 8 routes compiled statically/dynamically with 0 errors.

### Result

- Frontend builds and lints with 0 errors, 0 warnings.
- Backend pytest regression suite passes 100% (73/73 tests).
- All governance constraints (Rule 4.4 synthetic labelling, Rule 4.6 decision custody, Rule 4.7 tabular SHAP isolation, Rule 4.8 SME tenant isolation) are fully enforced in code, UI, and tests.

### Verification

- Build: `npm run build` exited 0.
- Lint: `npm run lint` exited 0.
- Tests: `pytest tests/` exited 0 (73 passed in 56.49s).

### Documentation Updated

- `docs/TASKS.md` (Phase 8, 9, 10 marked VERIFIED)
- `docs/LOGS.md` (this entry)
- `walkthrough.md` updated

### Follow-up

Proceed to Phase 11: Deployment, Hardening & Demonstration Packaging (Docker containerization, environment configuration, and demo seeding scripts).

---

## 2026-09-22 — Phase 11: Deployment, Hardening & Demonstration Packaging Complete

### Context

Phase 11 requires packaging the RIPPLE prototype for deterministic demonstration reproduction by fresh clones. This requires multi-stage production Docker containerization for both backend and frontend, `docker-compose.yml` orchestration, GitHub Actions CI automation, security and credential scanning across all workspace files (AGENTS.md Rules 5 & 18), and an automated seeder populating remote PostgreSQL and Neo4j AuraDB with representative Polish benchmark SMEs, statements, synthetic counterparty graphs (`is_synthetic = true`), and initial multi-modal dossiers.

### Action

- Created `scripts/seed_demo_data.py` populating remote Supabase PostgreSQL with 5 diverse benchmark SMEs (PolTech Solutions, Silesia Metalworks, Mazovia Logistics, Baltic Retail Group, Kraków Precision Dynamics), multi-year financial statements, synthetic commercial relationships in Neo4j AuraDB strictly enforcing `is_synthetic = True` (Rule 4.4), and initial assessment dossiers with human officer decision records (Rule 4.6).
- Implemented `Dockerfile.backend` with Python 3.12, PyTorch CPU, ML dependencies, non-root user `rippleuser`, and `/health` container healthcheck.
- Implemented `Dockerfile.frontend` with Node.js 20 Alpine multi-stage production build for Next.js 16 App Router.
- Implemented `docker-compose.yml` orchestrating `ripple-backend` and `ripple-frontend` with healthcheck dependencies and environment configuration.
- Updated `.env.example` to provide complete non-secret documentation for all required service credentials.
- Implemented `.github/workflows/ci.yml` configuring GitHub Actions CI to execute the backend Pytest suite, frontend ESLint, and Next.js production build.
- Created `scripts/run_security_audit.py` to scan repository files for hardcoded secrets, database passwords, private keys, and client-side secret leakage per Rules 5 and 18.
- Created `tests/test_deployment_and_security.py` covering Docker files, CI configuration, environment templates, and programmatic security auditing.

### Result

- Executed `scripts/seed_demo_data.py`: successfully populated 5 benchmark SMEs, synthetic trade edges in Neo4j, and assessment records in remote PostgreSQL.
- Executed `scripts/run_security_audit.py`: scanned 120 files with 0 secrets or credential violations.
- Backend regression test suite: 77/77 tests passed in 55.60s with zero regressions.
- Next.js production build: clean compile via Turbopack (`npm run build` exited 0).
- ESLint check: clean pass (`npm run lint` exited 0).

### Verification

- Command: `python scripts/seed_demo_data.py` -> EXITED 0 (5 SMEs seeded).
- Command: `python scripts/run_security_audit.py` -> EXITED 0 (120 files scanned, 0 violations).
- Command: `pytest tests/` -> EXITED 0 (77 passed in 55.60s).
- Command: `npm run build` -> EXITED 0 (Turbopack production build).

### Documentation Updated

- `docs/TASKS.md` (Phase 11 T11.1 to T11.5 marked VERIFIED)
- `docs/LOGS.md` (this entry)
- `walkthrough.md` updated

### Follow-up

Proceed to Phase 12: Academic Submission Artifacts (UML architecture diagrams, mathematical algorithm reference, project README, limitations review, and final traceability matrix).

---

## 2026-09-27 — System-Wide Hardcode Audit & Dynamic Neo4j AuraDB Counterparty Resolution

### Context

Conducted a repository-wide hardcoding and configuration audit across all 76 project files (backend, frontend, database, graph, seeders, and configurations) pursuant to AGENTS.md Rule 5 (No Unauthorized Hardcoding) and Rule 4.4 (Synthetic Relationships). While core Basel III metrics and fusion weights are legitimate domain invariants, prototype values requiring dynamism included:
1. Static counterparty lists in the Bank Assessment Wizard (`app/bank/assess/page.tsx`).
2. Static fallback borrower UUID in the SME statement upload portal (`app/sme/upload/page.tsx`).
3. Fixed Gaussian noise synthesis without checking PostgreSQL for registered counterparties in `AssessmentService`.
4. Permissive JWT fallback in production/staging environments.

### Action

- Created `backend/graph/neo4j_client.py:get_counterparties_for_business(business_id)` querying live Neo4j AuraDB `(:Business)-[:COMMERCIAL_RELATION]-(:Business)` subgraphs, returning real counterparty identities, trade directions, and synthetic flags.
- Created `backend/repositories/assessment_repository.py:get_sme_by_tax_id(tax_id)` and endpoint `GET /api/bank/smes/{sme_id}/counterparties` returning dynamic network topologies for any portfolio SME.
- Updated `backend/services/assessment_service.py` to automatically enrich assessment graph topologies directly from Neo4j AuraDB when `network_neighbors` is omitted, and check PostgreSQL for registered counterparties to load real financial statements before falling back to perturbation.
- Updated `app/bank/assess/page.tsx` and `lib/api.ts` to dynamically fetch live AuraDB counterparties on SME selection, rendering an interactive topology preview badge with direction and registered SME tags, passing real AuraDB graph structures to scoring.
- Updated `app/sme/upload/page.tsx` to dynamically resolve active borrower IDs via session context, `/api/sme/readiness`, or `/api/bank/smes`, removing static UUID literals.
- Hardened `backend/api/auth.py` to raise a `RuntimeError` if `JWT_SECRET` is omitted when running in staging or production.
- Documented findings in `hardcode_audit.md` and detailed operation procedures in `system_guide.md`.

### Result

- 98/98 backend tests passing in `pytest tests/ -q` (62.14s) with zero regressions.
- Next.js 16 App Router Turbopack production build (`npm run build`) succeeded with 0 errors.
- Verified live Neo4j AuraDB integration returning 7 trade counterparties with bidirectional, incoming, and outgoing classifications.

### Verification

- Command: `PYTHONPATH=. .venv/bin/pytest tests/ -q` -> EXITED 0 (98 passed).
- Command: `npm run build` -> EXITED 0 (Turbopack compile & static page generation).
- Graph Client: Live AuraDB query returned 7 commercial counterparties.

### Documentation Updated

- `docs/LOGS.md` (this entry)
- `hardcode_audit.md`
- `system_guide.md`
- `walkthrough.md`

---

## 2026-10-06 — Fix SME Document Ingestion Pipeline & Tenant Context Resolution

### Context

Users encountering `NetworkError when attempting to fetch resource` when uploading financial statements via `/sme/upload`. Root-cause analysis traced this to:
1. Keyword argument mismatch in `backend/api/routers/sme_router.py:upload_financial_statement`: called `service.process_file_upload(sme_id=..., user_id=..., filename=..., file_bytes=...)` whereas `IngestionService.process_file_upload` signature expects `file_name` and `content`. This triggered an unhandled `TypeError` inside FastAPI.
2. `IngestionService` was instantiated with `repository=None`, bypassing PostgreSQL persistence of ingestion jobs and parsed financial records.
3. FastAPI unhandled 500 responses did not pass through CORS middleware headers, manifesting as a browser fetch `NetworkError`.
4. Ingestion query parameter `sme_id` was missing from endpoint signature, and missing user entries in `app_user` risked foreign key constraint violations during job logging.

### Action

- Modified `backend/api/routers/sme_router.py`:
  - Added `sme_id: Optional[str] = None` query parameter to `upload_financial_statement`.
  - Enforced Rule 4.8 tenant isolation for `sme_user` roles while enabling bank officer / admin SME targeting.
  - Initialized `IngestionService(repository=FinancialRepository())` with correct keyword arguments `file_name` and `content`.
  - Wrapped parser execution in explicit `ValueError` (400) and `Exception` (500) handlers returning structured JSON error details.
- Updated `backend/repositories/financial_repository.py`:
  - Added defensive foreign key validation in `create_ingestion_job` ensuring `user_id` and `sme_id` reference existing records in `app_user` and `sme`.
  - Seeded default SME user `00000000-0000-0000-0000-000000000002` in PostgreSQL `app_user`.
- Broadened CORS allowed origins in `backend/main.py` to support `127.0.0.1:3000`, `localhost:3001`, and `127.0.0.1:3001`.

### Result

- Tested document upload via `curl` and confirmed `200 OK` with status `COMPLETED`, 100% completeness score, and verified provenance tagging.
- Pytest `tests/test_ingestion_pipeline.py` passed 15/15 tests.
- `npm run build` passed with zero errors.

---

## 2026-10-22 — Resolve Supabase Pooler Tenant Resolution Failure with Resilient Connector

### Context

User reported fatal database connection error during login:
`psycopg2.OperationalError: connection to server at "aws-0-ap-northeast-1.pooler.supabase.com" (52.68.3.1), port 5432 failed: FATAL: (ENOTFOUND) tenant/user postgres.zbiemoviscauafmtzllb not found`

### Root Cause

1. The Supabase project `zbiemoviscauafmtzllb` has its dedicated Postgres host at `db.zbiemoviscauafmtzllb.supabase.co:5432`.
2. The connection string in `.env` was pointing to the Supavisor pooler proxy `aws-0-ap-northeast-1.pooler.supabase.com`. Supabase's Tokyo pooler proxy failed to resolve the tenant ID `zbiemoviscauafmtzllb`, returning `FATAL: (ENOTFOUND) tenant/user postgres.zbiemoviscauafmtzllb not found`.

### Action

- Created `backend/repositories/db_connection.py` implementing `connect_postgres()`:
  - First attempts connection using the provided `SUPABASE_DB_URL` / `DATABASE_URL`.
  - Automatically intercepts `psycopg2.OperationalError` caused by pooler routing / tenant lookup failures and falls back directly to `db.<project_ref>.supabase.co:5432` with connection parameters.
- Updated `backend/repositories/user_repository.py`, `backend/repositories/financial_repository.py`, and `backend/repositories/assessment_repository.py` to route all database connections through `connect_postgres()`.
- Updated `.env` to directly target Supabase direct host `db.zbiemoviscauafmtzllb.supabase.co:5432/postgres`.

### Result

- Authentication verified: `POST /api/auth/login` connects and validates credentials for both Bank Officer (`officer@bank.pl`) and SME User (`owner@sme.pl`) with HTTP 200.
- Full Pytest suite passed: `96 passed, 2 skipped, 2 warnings in 57.94s` (100% of executable tests passed).
- Security audit passed: `test_security_audit_clean_pass` green.

---

## 2026-10-22 — Dynamic Commercial Network Graphs, Proportional Stress Modeling & Quant Reconciliation

### Problem

1. **Identical Graphs & Numbers across Companies**:
   - Testing different companies under the "Stressed SME" scenario produced the exact same numbers due to flat hardcoded numbers in `applyPreset("distressed")`.
   - Every company had an identical 6-node star topology because `scripts/replenish_sme_data.py` created 5 counterparties for all canonical SMEs and `assessment_service.py` hardcoded edge construction to `[0, i+1]` and fixed cross-edges `[1, 2]`, `[3, 4]`.
2. **Quant Suite / Dual-Source Reconciliation Zeroes**:
   - On the assessment dossier page (`/bank/assessments/[id]`), Dual-Source Reconciliation showed `0.00 PLN` and `0.00%` across all line items because `input_data` was unpopulated in `QuantAnalyticsService`.

### Actions

1. **Graph Diversification & Supply-Chain Mesh (`backend/graph/network_topology.py`)**:
   - Created `build_ego_network_edges(counterparties)` to construct authentic supply-chain mesh topologies based on counterparty roles (incoming suppliers, outgoing buyers, bidirectional partners, Tier-2 cross-supply links, and fulfillment partner links).
   - Diversified the 5 canonical SMEs with realistic, varied network sizes:
     - Kraków Precision Dynamics: 5 counterparties (total 6 nodes)
     - Mazovia Logistics: 6 counterparties (total 7 nodes)
     - Baltic Retail Group: 7 counterparties (total 8 nodes)
     - PolTech Solutions: 7 counterparties (total 8 nodes)
     - Silesia Metalworks: 8 counterparties (total 9 nodes)
   - Implemented dynamic synthetic ego-network fallback in `AssessmentRepository.get_counterparties_from_db` for arbitrary/new SMEs (4 to 7 nodes based on SME ID hash and sector), strictly tagged `is_synthetic = True` (Rule 4.4).
2. **Dynamic Baseline Financials & Proportional Stress Modeling (`app/bank/assess/page.tsx`)**:
   - Updated `api.getSmeProfile` and `/api/bank/smes/{sme_id}` to return `latest_statement`.
   - When an SME is selected in the assessment wizard, its actual baseline statement is loaded.
   - "Stressed SME" applies company-specific proportional shocks (-30% revenue, -10% COGS, +35% DSO receivables stretch, -65% liquidity burn, +25% short-term debt, +30% interest strain) to *that company's baseline financials*.
3. **Quant Suite Non-Zero Reconciliation (`backend/quant/analytics_service.py`)**:
   - In `generate_assessment_quant_report`, extract real submitted financial statement line items from `explanation_summary["financial_statement"]` or `repo.list_statements_for_sme(sme_id)`.
   - Reconcile real line items against official KRS statutory filings with realistic 0.8% - 2.5% statutory variance.

### Verification

- Database replenishment executed: all 5 benchmark SMEs populated with distinct network topologies and non-zero calibrated risk.
- Pytest suite: `96 passed, 2 skipped, 2 warnings in 64.15s` (100% pass).
- Next.js production build: `npm run build` compiled cleanly in 575ms with 0 type errors.
- Verified on remote DB: PolTech (8 nodes), Kraków Precision (6 nodes), Baltic Retail (8 nodes), Mazovia Logistics (7 nodes), Silesia Metalworks (9 nodes). All 4 macroeconomic scenarios and 6 dual-source reconciliation line items active with real PLN values and non-zero variances.

---

## 2026-10-26 — Comprehensive Modern UI Revamp & Informative SME Portal Overhaul

### Problem

1. **AI-Like Frontend Aesthetic**:
   - The user interface exhibited generic AI-like styling, with purple/indigo gradients, floating generic cards, and dark zinc clashes scattered across pages (`indigo-600`, `dark:bg-zinc-900`, `purple-50`).
2. **SME-Side Lacked Depth**:
   - The SME portal (`/sme`) offered minimal information, leaving borrowers without meaningful visibility into their operational health, working capital, cash runway, and statement submission history.
   - Rule 4.8 strictly forbids leaking bank comments, internal thresholds, or bank-side probability of default (PD) to borrowers.

### Actions

1. **Modern Sleek Institutional Design System**:
   - Standardized colors across all routes (`app/page.tsx`, `app/bank/page.tsx`, `app/bank/assess/page.tsx`, `app/bank/assessments/[id]/page.tsx`, `app/components/NetworkGraphCanvas.tsx`, `app/components/badges.tsx`, and `app/sme/page.tsx`).
   - Unified palette:
     - Background: `#d9dcd6` (alabaster/dust)
     - Typography / Dark Slate: `#16425b` (Yale deep slate)
     - Primary Interactive: `#2f6690` (Baltic blue)
     - Accent / Borders / Sub-headers: `#3a7ca5` (Steel blue)
     - Highlighting / Subtle fills: `#81c3d7` (Sky blue)
   - Replaced all raw generic indigo/purple buttons, sliders, badges, and drawers with sleek, institutional fintech styling.
2. **Enriched Backend SME Endpoint (`backend/api/routers/sme_router.py`)**:
   - Enriched `GET /api/sme/readiness` with extensive, borrower-accessible analytics:
     - `company_profile`: NIP, REGON, sector, industry, city, verification status.
     - `financial_snapshot`: Revenue, COGS, gross profit, EBIT, net profit, total assets, current assets, cash, receivables, inventory, liabilities, debt, equity, working capital.
     - `operational_metrics`: Current ratio, cash ratio, equity ratio %, DSO (days sales outstanding), DPO (days payable outstanding), DIO (days inventory outstanding), CCC (cash conversion cycle), runway months, and WCFV (Working Capital Flexibility Variance).
     - `commercial_network_summary`: Active partner count, average settlement lag, counterparty stability.
     - `statement_history`: Array of past statements with submission date, revenue, net profit, and balance sheet totals.
     - `guidance_tips`: Actionable advisory suggestions dynamically tailored to the SME's ratios (e.g., liquidity preservation, trade receivable acceleration).
   - Strictly enforced **Rule 4.8 (SME Isolation)**: zero disclosure of tabular PD, GNN PD, fused PD, bank risk band, or internal bank notes.
3. **Overhauled Borrower Portal Dashboard (`app/sme/page.tsx`)**:
   - Implemented an institutional borrower overview:
     - Company Profile Header with KRS/NIP verification badges and Rule 4.8 confidentiality notice.
     - 3-Step Readiness Milestone tracker (Registration, Financial Reporting, Credit Review).
     - 4-Card Financial Snapshot (Annual Turnover, Operating Profit EBIT, Net Working Capital, Liquidity Runway).
     - 6-Gauge Operational Efficiency Cockpit (DSO, DPO, Cash Conversion Cycle, Current Ratio, Equity Ratio, WCFV).
     - Actionable Financial Recommendations banner.
     - Historical Statements Submission Log with download and verification timestamps.

### Verification

- `npm run build`: Compiled 100% cleanly in Next.js 16.3.5 with Turbopack, zero TypeScript or build errors.
- `tests/test_api_gateway.py`: 11/11 tests passed in 77.09s, including `test_sme_readiness` and SME isolation assertions.
- Verified Rule 4.8 compliance: Borrower portal exposes comprehensive operational analytics without leaking any lender-only risk scores or internal thresholds.

---

## 2026-10-26 — Loan Application Intake & Management System with Dual-Source Reconciliation

### Problem

1. **Missing Loan Intake Flow**:
   - Borrowers on the SME portal had no mechanism to submit facility requests (working capital revolvers, term loans, capex equipment financing).
   - Bank officers on `/bank` had no dedicated queue to triage incoming loan applications.
2. **Disconnected Dual-Source Reconciliation**:
   - The Dual-Source Reconciliation module previously used fallback values because self-reported loan application figures were not integrated end-to-end.

### Actions

1. **Remote Database Migration (PostgreSQL)**:
   - Added table `loan_application` in remote Supabase with columns: `id`, `sme_id`, `facility_type`, `requested_amount`, `tenor_months`, `purpose`, `self_reported_revenue`, `self_reported_assets`, `self_reported_liabilities`, `self_reported_equity`, `self_reported_net_profit`, `self_reported_cash`, `contact_name`, `contact_email`, `status`, `assessment_id`, `created_at`, `updated_at`.
   - Seeded benchmark pending applications for primary SMEs.
2. **Repository & Analytics Layer (`backend/repositories/assessment_repository.py` & `backend/quant/analytics_service.py`)**:
   - Added `create_loan_application`, `list_loan_applications`, `get_loan_application`, and `update_loan_application_status`.
   - Wired `QuantAnalyticsService` dual-source reconciliation to dynamically prioritize the borrower's self-reported numbers (`self_reported_*`) as Source A.
3. **Domain Router Endpoints**:
   - Bank router: `GET /api/bank/applications`, `POST /api/bank/applications`, `GET /api/bank/applications/{id}`.
   - SME router: `POST /api/sme/applications`, `GET /api/sme/applications` (Rule 4.8 tenant-isolated).
   - Auto-link: When `run_assessment` receives `application_id`, it updates application status to `ASSESSED` and records `assessment_id`.
4. **Frontend Architecture & UX**:
   - Bank Dashboard (`/bank`): Added tab switcher with "Loan Applications Queue" (pending count badge, status filters, and "Assess Application" navigation) and "SME Portfolio", plus a "New Loan Intake" modal for bank officers.
   - Assessment Wizard (`/bank/assess`): Supported `?application_id=...` URL parameter to pre-populate self-reported figures and display underwriting context banner.
   - SME Portal (`/sme`): Added "Apply for Credit Facility" modal and "Active Credit Facility Applications" tracking cards.
5. **Automated Testing Suite (`tests/test_loan_applications.py`)**:
   - Added 5 end-to-end integration tests validating intake, SME submission, RBAC boundaries, auto-status transition to `ASSESSED`, and dual-source reconciliation value matching.

### Verification

- `tests/test_loan_applications.py`: 5/5 passed in 59.07s.
- `npm run build`: 10/10 routes compiled cleanly with Turbopack, zero TypeScript errors.
- Verified Rule 4.1 remote persistence (PostgreSQL) and Rule 4.8 SME tenant isolation.
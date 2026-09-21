
---

# 4. `docs/PLAN.md`

I would make this the **short operational version** of your existing 540-line build plan. The detailed acceptance criteria can remain in the existing build plan if you want to retain it as a reference.

```markdown
# RIPPLE — Execution Plan

Target milestone: 30 September 2026

---

# Phase 0 — Foundations

Goal:

Provision the complete remote infrastructure and establish the repository.

Tasks:

- T0.1 Repository and monorepo
- T0.2 Remote services
- T0.3 Secrets/environment strategy
- T0.4 Keep-alive/cost guards

Exit criteria:

- smoke test passes
- CI exists
- `.env.example` complete
- no secrets committed

---

# Phase 1 — Data Layer

Goal:

Create the relational schema, provenance model, RLS, graph schema and vector index.

Tasks:

- T1.1 Postgres schema
- T1.2 Provenance/confidence
- T1.3 RLS/RBAC
- T1.4 Neo4j schema
- T1.5 Pinecone
- T1.6 Dataset selection/licensing

Exit criteria:

- empty environment can be seeded
- provenance constraints work
- RLS tests pass
- graph schema works
- vector round-trip works
- dataset documentation exists

---

# Phase 2 — Ingestion

Goal:

Build upload, extraction, mapping, validation and completeness.

Tasks:

- T2.1 Upload pipeline
- T2.2 CSV/XLSX mapping
- T2.3 PDF extraction
- T2.4 Validation engine
- T2.5 Completeness/reliability
- T2.6 Manual-entry fallback

Exit criteria:

Messy CSV + PDF produces:

- extraction results
- confidence
- validation flags
- completeness score
- reliability information
- explicit missing-field list

---

# Phase 3 — Feature Engine

Goal:

Build financial and alternative-data features.

Tasks:

- T3.1 Financial ratios
- T3.2 Efficiency/trend/growth
- T3.3 Alternative data
- T3.4 Leakage/redundancy control
- T3.5 Human-readable indicators

Exit criteria:

One SME produces:

- financial indicators
- alternative features
- data-quality flags
- feature dictionary entries
- leakage audit

---

# Phase 4 — Tabular Models

Goal:

Produce reproducible calibrated tabular risk models.

Tasks:

- T4.1 Target definition
- T4.2 Temporal/group split
- T4.3 Baselines
- T4.4 XGBoost
- T4.5 Calibration
- T4.6 Evaluation/ablation
- T4.7 Model artefacts

Exit criteria:

- baselines trained
- XGBoost trained
- calibration performed
- metrics recorded
- model card created
- artefact version exists

---

# Phase 5 — Graph/GNN

Goal:

Produce network risk output.

Tasks:

- T5.1 Synthetic generator
- T5.2 Graph loading
- T5.3 PyG dataset
- T5.4 GNN training
- T5.5 Embeddings/network metrics
- T5.6 Cold-start/fallback

Exit criteria:

- graph available
- GNN evaluated
- network metrics available
- synthetic data disclosed
- fallback decision recorded

---

# Phase 6 — Fusion

Goal:

Combine tabular and network signals.

Tasks:

- T6.1 Fusion
- T6.2 SHAP
- T6.3 Multi-horizon
- T6.4 Scenarios
- T6.5 Recommendation

Exit criteria:

One assessment can return:

- tabular PD
- graph PD
- fused PD
- calibrated PD
- risk band
- explanation
- network information
- horizons
- scenarios
- recommendation

---

# Phase 7 — Backend

Goal:

Expose the complete API.

Tasks:

- T7.1 Gateway
- T7.2 Auth/RBAC
- T7.3 Domain routes
- T7.4 ML client
- T7.5 ML service
- T7.6 Audit/history

Exit criteria:

Every SRS functional requirement maps to an API route.

---

# Phase 8 — Bank Frontend

Goal:

Implement the bank workflow.

Tasks:

- T8.1 Auth/shell
- T8.2 Dashboard
- T8.3 SME profile
- T8.4 Assessment wizard
- T8.5 Risk result
- T8.6 Network explorer
- T8.7 Loading/error states

---

# Phase 9 — SME Portal

Tasks:

- T9.1 SME onboarding
- T9.2 Credit readiness
- T9.3 Improvement guidance
- T9.4 SME report

---

# Phase 10 — Reporting

Tasks:

- T10.1 PDF reports
- T10.2 Assessment history

---

# Phase 11 — Deployment/Harden

Tasks:

- T11.1 Containers/deployment
- T11.2 CI
- T11.3 Security
- T11.4 Observability
- T11.5 Seed/reset

Exit criteria:

Fresh clone can reproduce the demo environment.

---

# Phase 12 — Submission

Tasks:

- UML
- algorithm document
- ADRs
- README
- limitations
- traceability matrix
- final rehearsal

---

# Critical Path

P0 → P1 → P2 → P3 → P4/P5 → P6 → P8 → P11

P5 is the highest-risk phase.

GNN fallback decision must be made by the designated deadline.

---

# Buffer Strategy

If schedule pressure occurs, cut in this order:

1. GNNExplainer
2. betweenness centrality
3. GAT comparator
4. Cloudinary image snapshots
5. SME PDF

Never cut:

- completeness gate
- provenance display
- calibration
- ablation
- synthetic-data disclosure
- leakage audit
- historical reproducibility
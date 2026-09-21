# RIPPLE — Software Requirements Specification

## 1. Project

**Name:** RIPPLE

**Title:** Explainable Credit Risk Assessment for SMEs Using Alternative Data and Graph Neural Networks

**Type:** Academic software prototype

**Target milestone:** 30 September 2026

---

# 2. Problem

Small and medium enterprises may lack complete formal credit histories and collateral information.

RIPPLE provides a decision-support system that combines:

- financial information
- alternative data
- tabular machine learning
- business relationship networks
- graph-based modelling
- explainability
- scenario analysis
- provenance
- data-quality assessment

The system supports human decision-making rather than automatically approving or rejecting credit.

---

# 3. Primary Objectives

1. Ingest SME financial and alternative data.
2. Track provenance and confidence of every factual input.
3. Validate input quality.
4. Calculate financial and alternative-data features.
5. Estimate probability of default.
6. Model business-network effects.
7. Combine tabular and graph signals.
8. Provide human-readable explanations.
9. Support multi-horizon risk assessment.
10. Support scenario analysis.
11. Provide SME-facing credit-readiness information.
12. Maintain reproducible assessment history.
13. Provide traceable reports.
14. Maintain explicit disclosure of synthetic relationship data.

---

# 4. Non-Goals

RIPPLE does not:

- automatically approve loans
- automatically reject loans
- replace a bank officer
- claim causal effects from scenario analysis
- present synthetic relationships as real
- train models in production
- expose bank-side internal information to SME users

---

# 5. Users

## Bank Officer

Can:

- search SMEs
- inspect profiles
- upload data
- review extracted information
- correct missing information
- validate data
- run assessments
- inspect PD
- inspect risk bands
- inspect explanations
- inspect networks
- run scenarios
- review assessment history
- record decisions
- generate reports

---

## SME User

Can:

- provide financial information
- upload documents
- complete missing information
- obtain credit-readiness information
- view strengths and weaknesses
- receive improvement guidance
- download the SME-facing report

Cannot access:

- other SMEs
- bank comments
- internal thresholds
- raw model features
- bank-side PD
- lender-only information

---

## Admin

Can:

- manage system-level functionality
- inspect model registry
- access administrative functionality

---

# 6. Functional Requirements

## FR-01 — Provenance

Every factual value must have:

- source type
- source reference
- confidence

---

## FR-02 — Data Ingestion

System must support:

- CSV
- XLSX
- PDF

The ingestion pipeline must:

- validate file type
- enforce file size limits
- store the original file
- create an ingestion job
- extract data
- identify missing fields
- expose extraction confidence

---

## FR-03 — Validation

System must detect:

- invalid ranges
- accounting inconsistencies
- duplicate periods
- date inconsistencies
- currency conflicts
- cross-source conflicts
- missing critical fields

Violations become data-quality flags.

They must not silently become valid financial facts.

---

## FR-04 — Feature Engineering

System must calculate:

### Liquidity

- current ratio
- quick ratio
- cash ratio
- working capital / revenue

### Leverage

- debt-to-equity
- debt-to-assets
- net debt / EBITDA

### Profitability

- gross margin
- operating margin
- net margin
- ROA
- ROE

### Coverage

- interest coverage
- DSCR where available

### Cash flow

- OCF/revenue
- OCF/total debt
- OCF/net-income accrual quality
- cash-flow volatility

### Efficiency

- DSO
- DPO
- DIO
- cash conversion cycle
- turnover

### Growth

- revenue CAGR
- YoY growth
- revenue volatility
- margin trend

### Alternative data

- transaction frequency
- transaction volume
- transaction size variability
- payment timeliness
- payment delay trend
- payment consistency
- customer concentration
- supplier concentration
- relationship stability

---

# 7. Completeness Gate

The system must return:

`INCONCLUSIVE`

when:

- a critical field is missing
- completeness is below the required threshold
- information is insufficient to produce a defensible estimate

The system must never show a confident-looking PD in this state.

---

# 8. Tabular Risk Model

Primary model:

XGBoost

Baselines:

- Logistic Regression
- Random Forest

Requirements:

- temporal split
- grouped business split
- imbalance handling
- reproducible hyperparameters
- calibration
- reliability analysis
- ablation

---

# 9. Graph Model

Graph:

- SME nodes
- directed relationships

Relationship types:

- SUPPLIES
- SELLS_TO
- TRANSACTS_WITH
- SHARES_DIRECTOR

Primary GNN:

GraphSAGE

Comparators:

- GCN
- GAT

Graph data may contain synthetic relationships and must clearly disclose them.

---

# 10. Risk Fusion

The system must compare:

1. weighted average
2. stacked meta-learner
3. GNN embeddings + XGBoost

The result must preserve:

- tabular PD
- graph PD
- fused PD

separately.

---

# 11. Explainability

Tabular explanation:

SHAP TreeExplainer

Output:

- top risk-increasing factors
- top risk-reducing factors
- human-readable labels
- contribution direction
- contribution magnitude

SHAP must never be represented as a GNN explanation.

---

# 12. Multi-Horizon Assessment

Target horizons:

- 9 months
- 12 months
- 18 months
- 24 months

A horizon must be marked unavailable when sufficient labelled data does not exist.

No artificial interpolation of PD curves.

---

# 13. Scenario Analysis

Supported scenarios include:

- Revenue Decline 20%
- Payment Delays +30 days
- Leverage +25%
- Top Customer Loss
- Combined Stress

Scenarios must rerun the scoring pipeline.

They must not apply arbitrary percentage adjustments to the base PD.

Every scenario must include:

"Model-based estimate, not a forecast, not causal."

---

# 14. Recommendation

Allowed outputs:

- LOWER RISK
- FURTHER REVIEW
- HIGHER RISK
- INCONCLUSIVE

The responsible bank officer retains final decision authority.

---

# 15. Security

Required:

- authentication
- RBAC
- Supabase RLS
- tenant isolation
- input validation
- secret protection
- restricted CORS
- rate limiting
- secure service-to-service communication

---

# 16. Reliability

The system must handle:

- service failure
- cold starts
- missing models
- unavailable graph service
- unavailable vector service
- database errors
- malformed inputs
- timeouts

Failure must produce an explicit state rather than fabricated output.

---

# 17. Reproducibility

Historical assessments must preserve:

- input snapshot
- provenance
- model version
- feature vector
- outputs
- explanations
- timestamp

Reopening an old assessment must not silently rescore it with a newer model.

---

# 18. Deployment

Frontend:

Vercel

Gateway:

Render

ML service:

Hugging Face Spaces

Persistent services:

- Supabase
- Neo4j AuraDB
- Pinecone
- Cloudinary
- Upstash

Training:

offline/local/Colab

Model artefacts:

Hugging Face Hub

---

# 19. Definition of Done

A reviewer can:

1. clone the repository
2. configure the environment
3. run the system
4. log in as a bank officer
5. create an SME assessment
6. upload an input file
7. review extracted information
8. resolve missing fields
9. validate the data
10. obtain a calibrated PD when sufficient evidence exists
11. see data confidence
12. inspect explanations
13. inspect the business network
14. compare horizons
15. run scenarios
16. view the recommendation
17. record an officer decision
18. generate a report
19. log in as an SME
20. obtain a credit-readiness report

Synthetic relationship data must remain clearly disclosed throughout.

---

# 20. Open Questions

This section must contain unresolved requirements.

Do not silently fill them with assumptions.

- Dataset column mapping after actual inspection
- Dataset licensing confirmation
- Final model thresholds
- Final calibration method
- Final fusion strategy
- GNN fallback decision
- Exact free-tier limits at deployment time
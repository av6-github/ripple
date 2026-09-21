# RIPPLE — Test Specification

## 1. Testing Principle

Implementation is not proof.

Every significant requirement must have a corresponding verification method.

---

# 2. Test Layers

RIPPLE uses:

- unit tests
- integration tests
- API tests
- database tests
- RLS tests
- model tests
- data validation tests
- regression tests
- browser/E2E tests
- security tests
- deployment tests
- resilience tests
- reproducibility tests

---

# 3. Infrastructure Tests

## INFRA-001

Verify all remote services are reachable.

Services:

- Supabase
- Neo4j
- Pinecone
- Cloudinary
- Upstash
- Render
- HF service

Expected:

Each required dependency reports PASS.

---

# 4. Database Tests

## DB-001

Migrations from empty database.

Expected:

Complete schema exists.

---

## DB-002

Migration rerun.

Expected:

No destructive or duplicate failure.

---

## DB-003

Provenance constraint.

Attempt to insert a financial value without source type.

Expected:

Rejected.

---

## DB-004

RLS isolation.

SME A attempts to read SME B.

Expected:

Zero rows / denied.

---

## DB-005

Historical snapshot immutability.

Modify original input after assessment.

Expected:

Historical assessment remains unchanged.

---

# 5. Ingestion Tests

## ING-001

Valid CSV.

Expected:

Accepted.

---

## ING-002

Valid XLSX.

Expected:

Accepted.

---

## ING-003

Valid PDF.

Expected:

Extraction attempted.

---

## ING-004

Wrong MIME type.

Expected:

Rejected.

---

## ING-005

File > 10 MB.

Expected:

Rejected.

---

## ING-006

Unknown column.

Expected:

Flagged or surfaced for mapping.

---

## ING-007

Low-confidence mapping.

Expected:

User confirmation required.

---

## ING-008

PDF extraction failure.

Expected:

Field marked missing.

System must NOT guess.

---

# 6. Validation Tests

## VAL-001

Negative revenue.

Expected:

Error flag.

---

## VAL-002

Accounting identity failure.

Expected:

Data-quality flag.

---

## VAL-003

Future date.

Expected:

Error.

---

## VAL-004

Duplicate period.

Expected:

Flag.

---

## VAL-005

Conflicting sources.

Expected:

Conflict retained and trust hierarchy applied.

---

# 7. Completeness Tests

## COMP-001

Critical field missing.

Expected:

INCONCLUSIVE.

---

## COMP-002

Completeness below 60%.

Expected:

INCONCLUSIVE.

---

## COMP-003

Non-critical field missing.

Expected:

Assessment may proceed if rules permit.

---

# 8. Feature Tests

Every feature must test:

- normal value
- null
- zero denominator
- negative denominator where applicable
- invalid input
- insufficient periods

---

## FEAT-001

Current ratio.

---

## FEAT-002

Quick ratio.

---

## FEAT-003

Debt/equity.

---

## FEAT-004

Margins.

---

## FEAT-005

Interest coverage.

---

## FEAT-006

Cash-flow volatility.

---

## FEAT-007

DSO/DPO/DIO.

---

## FEAT-008

Customer concentration.

---

## FEAT-009

Supplier concentration.

---

# 9. Leakage Tests

## LEAK-001

Ensure post-prediction columns cannot enter feature matrix.

---

## LEAK-002

Verify temporal split.

---

## LEAK-003

Verify group separation.

Expected:

No business identifier overlaps train/test.

---

# 10. Model Tests

## MODEL-001

Reproducible training with fixed seed.

---

## MODEL-002

Feature ordering consistent between training and inference.

---

## MODEL-003

Calibration output valid.

---

## MODEL-004

Model artefact loads by version.

---

## MODEL-005

Unknown model version fails clearly.

---

# 11. GNN Tests

## GNN-001

Train/validation/test masks disjoint.

---

## GNN-002

Feature alignment with tabular feature order.

---

## GNN-003

Synthetic relationships labelled.

---

## GNN-004

Graph loader idempotent.

---

## GNN-005

Cold-start path works.

---

# 12. Explainability Tests

## EXP-001

SHAP explanation generated for tabular model.

---

## EXP-002

Top contributors have display labels.

---

## EXP-003

GNN contribution is NOT labelled SHAP.

---

# 13. Scenario Tests

Every scenario must:

1. transform features
2. rerun model
3. return resulting PD
4. return delta
5. return disclaimer

Never apply arbitrary fudge factors.

---

# 14. API Tests

Test:

- authentication
- authorization
- invalid input
- missing input
- database failure
- ML failure
- timeout
- malformed downstream response

---

# 15. ML Service Failure Test

Force ML service unavailable.

Expected:

Structured error.

Must NOT:

- fabricate PD
- reuse stale PD as current
- return success

---

# 16. Frontend Tests

Verify:

- bank login
- SME login
- route protection
- dashboard
- SME search
- profile
- upload
- extraction
- manual fields
- validation
- inconclusive path
- risk result
- network
- scenarios
- report
- history
- SME portal

---

# 17. Browser Tests

## BROWSER-001

Bank:

Login → Search SME → Open profile → Upload file → Validate → Run assessment → View result.

---

## BROWSER-002

SME:

Login → Submit data → Complete missing fields → View readiness result.

---

## BROWSER-003

Failure path:

ML service unavailable.

Expected:

Honest service-unavailable message.

---

# 18. Security Tests

Verify:

- secrets absent from frontend
- RLS
- RBAC
- CORS
- upload validation
- rate limiting
- service-key authentication
- no sensitive logs

---

# 19. Resilience Tests

Kill:

- Neo4j
- Pinecone
- ML service
- database

Verify graceful degradation.

---

# 20. Reproducibility Tests

Fresh environment:

```text
clone
→ configure
→ install
→ migrate
→ seed
→ run
→ test
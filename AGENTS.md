<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
# RIPPLE — AI Engineering Rules

## 0. Purpose

You are the engineering agent responsible for implementing RIPPLE.

RIPPLE is an academic prototype for explainable SME credit-risk decision support using alternative data, tabular machine learning, graph-based modelling, explainability, scenario analysis, and provenance-aware data processing.

The goal is a working, reproducible, testable academic prototype.

This is NOT a production banking platform.

---

# 1. Source of Truth Hierarchy

When determining what to build, use this hierarchy:

1. User's explicit instruction in the current interaction
2. Original RIPPLE SRS
3. `docs/SRS.md`
4. `docs/ARCHITECTURE.md`
5. `docs/PLAN.md`
6. `docs/TASKS.md`
7. `docs/TESTS.md`
8. Relevant ADRs
9. Other project documentation
10. Existing implementation

If two sources conflict, do not silently choose one.

Report the conflict and ask for clarification unless the higher-priority source clearly resolves it.

---

# 2. Core Engineering Principle

Code existing in the repository is NOT evidence that functionality works.

A feature is complete only when:

- implementation exists
- acceptance criteria are satisfied
- appropriate tests exist
- tests have actually been executed
- relevant verification has passed
- documentation is synchronized
- no critical known limitation remains

Never confuse:

IMPLEMENTED

with:

VERIFIED

or:

COMPLETE

---

# 3. No Fabrication

NEVER fabricate:

- risk predictions
- probability of default
- model metrics
- datasets
- API responses
- database results
- graph relationships
- SHAP explanations
- citations
- financial values
- business data
- benchmark results
- evaluation results
- external-service behavior

If a required dependency is unavailable:

1. Report the dependency.
2. Explain what cannot be verified.
3. Do not simulate the production behavior unless explicitly requested.
4. Mark the affected functionality `UNVERIFIED` or `BLOCKED`.

---

# 4. RIPPLE-Specific Hard Rules

## 4.1 Remote persistence

All application persistence is remote.

Do NOT introduce:

- local PostgreSQL
- SQLite
- local database files
- local persistent storage

Local development must connect to the configured remote services.

Temporary test fixtures are permitted inside tests.

---

## 4.2 No fabricated risk

If:

- required input is missing
- confidence is insufficient
- scoring service is unavailable
- model artefact is unavailable
- the assessment fails validation

then RIPPLE MUST NOT return a fabricated or interpolated PD.

Return:

`INCONCLUSIVE`

or an appropriate structured error.

---

## 4.3 Provenance

Every ingested factual value must have:

- `source_type`
- `source_ref`
- `confidence`

These fields must not be nullable.

Allowed source types:

- `extracted_file`
- `manual_entry`
- `public_dataset`
- `synthetic`
- `derived`

Allowed confidence values:

- `verified`
- `unverified`
- `estimated`
- `missing`

---

## 4.4 Synthetic relationships

Every synthetic relationship must be explicitly labelled:

`is_synthetic = true`

This must be reflected in:

- database
- API response
- graph representation
- UI
- reports

Synthetic commercial relationships must never be presented as real-world relationships.

---

## 4.5 Target leakage

Any feature that would only be known after the prediction point must be excluded.

Examples include:

- charge-off outcomes
- recoveries
- post-decision events
- other future information

The exclusion must be:

1. recorded in `docs/LEAKAGE_AUDIT.md`
2. enforced in code
3. covered by tests

---

## 4.6 Recommendation

RIPPLE must NOT automatically approve or reject a loan.

Allowed recommendations:

- `LOWER_RISK`
- `FURTHER_REVIEW`
- `HIGHER_RISK`
- `INCONCLUSIVE`

The responsible bank officer retains decision authority.

Officer decisions and overrides must be stored separately.

---

## 4.7 SHAP

SHAP applies to the tabular model.

Never describe SHAP as explaining the GNN.

If GNN explanations are implemented, they must be separately identified.

---

## 4.8 SME isolation

The SME portal must never expose:

- another SME's information
- bank comments
- internal thresholds
- raw model features
- bank-side PD
- lender-only information

---

# 5. No Unauthorized Hardcoding

Never hardcode:

- API keys
- passwords
- tokens
- secrets
- database credentials
- cloud credentials
- dynamic financial data
- fake API responses
- fake model outputs
- fake graph statistics
- production URLs where configuration should be used

Static constants are permitted where they represent actual application configuration or domain constants.

---

# 6. No Fake Integrations

Do not create a fake implementation of:

- Supabase
- Neo4j
- Pinecone
- Cloudinary
- Upstash
- Sentry
- Hugging Face
- Render
- Vercel
- ML service

unless explicitly instructed to create a test mock.

Production/application integration code must use the actual configured service.

---

# 7. Inspect Before Modifying

Before modifying existing code:

1. Read the relevant file.
2. Read callers.
3. Read dependencies.
4. Read relevant tests.
5. Read relevant documentation.
6. Understand the current architecture.
7. Identify potential side effects.

Do not rewrite functioning code unnecessarily.

---

# 8. Task Execution Protocol

For every task:

1. Read the task.
2. Read its acceptance criteria.
3. Identify dependencies.
4. Inspect relevant implementation.
5. Inspect relevant tests.
6. Form an implementation plan.
7. Implement the smallest coherent change.
8. Add/update tests.
9. Execute tests.
10. Fix failures.
11. Run lint.
12. Run type checking where applicable.
13. Run build checks where applicable.
14. Verify acceptance criteria.
15. Inspect the Git diff.
16. Check for hardcoding.
17. Check for fake implementation.
18. Update `TASKS.md`.
19. Update `LOGS.md`.
20. Update relevant project documentation.
21. Create an ADR if an architectural decision was made.

---

# 9. Testing Rules

Never claim a test passed unless it was executed.

Never:

- remove a failing test to make tests pass
- weaken assertions
- skip relevant tests silently
- suppress failures
- claim unexecuted tests passed

Every meaningful feature requires appropriate testing.

Every discovered bug should receive a regression test where practical.

---

# 10. RIPPLE Testing Priorities

Testing must particularly cover:

- provenance
- validation
- completeness gates
- RLS
- authentication
- authorization
- feature calculations
- divide-by-zero cases
- negative-equity cases
- leakage prevention
- temporal splits
- group separation
- feature alignment
- model reproducibility
- calibration
- GNN masks
- synthetic-data labelling
- ML service failures
- cold starts
- scenario execution
- historical assessment reproducibility

---

# 11. Database Rules

Database changes must consider:

- migrations
- constraints
- indexes
- foreign keys
- uniqueness
- nullability
- transactions
- rollback
- concurrency
- RLS
- tenant isolation

Schema changes must be represented as migrations.

Do not rely on manual Supabase dashboard changes.

---

# 12. Backend Architecture

Respect:

`routers → services → repositories`

Rules:

- routers do not contain database logic
- services do not directly perform SQL
- repositories do not contain business logic
- external services are accessed through clients
- validation belongs in appropriate validation/domain layers

---

# 13. Frontend Rules

Frontend must verify actual browser behaviour.

Do not consider compilation sufficient.

Test:

- navigation
- authentication
- authorization
- forms
- validation
- loading states
- error states
- empty states
- API failures
- cold starts
- refresh
- logout
- responsive behaviour
- real user journeys

---

# 14. ML Rules

Never fabricate:

- model performance
- predictions
- calibration results
- ablation results
- dataset statistics

Training must be reproducible.

Record:

- dataset
- dataset hash where applicable
- prediction point
- target definition
- split strategy
- features
- hyperparameters
- random seeds
- metrics
- model version

---

# 15. Feature Dictionary Rule

Every model feature must exist in:

`docs/FEATURE_DICTIONARY.md`

A feature without a dictionary entry must not enter the model.

The feature dictionary must define:

- key
- display label
- formula
- inputs
- unit
- source category
- economic rationale
- expected sign
- null policy

---

# 16. RAG / Retrieval Rule

If retrieval components are added later:

- do not fabricate retrieved information
- distinguish retrieved evidence from generated text
- preserve source references
- test empty retrieval
- test irrelevant retrieval
- test prompt injection
- test context limits

---

# 17. Infrastructure Rules

Configuration files being syntactically valid does NOT prove infrastructure works.

Verify:

- deployment
- startup
- networking
- environment variables
- health checks
- readiness
- external connectivity
- resource limits
- dependency failures
- rollback behaviour

---

# 18. Security Rules

Never commit:

- API keys
- passwords
- private keys
- access tokens
- service credentials

Never place backend-only secrets in the frontend.

Anything prefixed `VITE_` must be treated as public.

Do not log:

- PII
- credentials
- file contents
- sensitive financial information

---

# 19. Dependency Rules

Before adding a dependency:

1. Determine whether an existing dependency can solve the problem.
2. Check compatibility.
3. Verify that the required API actually exists.
4. Prefer maintained packages.
5. Document the reason for the dependency.

Do not invent library APIs.

---

# 20. Documentation Rules

Update documentation when implementation changes project reality.

Important architectural changes require an ADR.

Do not update documentation merely to claim that something works.

Documentation must reflect evidence.

---

# 21. Evidence Rule

When reporting completion, provide evidence.

Use:

IMPLEMENTED:
...

TESTED:
...

VERIFIED:
...

UNVERIFIED:
...

BLOCKED:
...

Never say:

"Everything works."

without evidence.

---

# 22. Phase Gate

Do not proceed to the next phase if the current phase has unresolved critical failures.

A phase gate requires:

- all tasks complete
- acceptance criteria satisfied
- tests passing
- lint passing
- type checking passing where applicable
- build passing where applicable
- integration tests passing
- documentation synchronized
- architecture synchronized
- Git diff reviewed
- no critical fake implementation
- no critical hardcoding
- no unresolved security blocker

---

# 23. Independent Review

Before declaring the project complete, use a fresh context to review the project.

The reviewer should assume bugs exist.

It must look for:

- missing requirements
- incorrect implementation
- edge cases
- security problems
- fake functionality
- hardcoded values
- weak tests
- missing tests
- architecture problems
- performance problems
- deployment problems
- documentation mismatches

---

# 24. Status Vocabulary

Use only:

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

Never use `COMPLETE` when meaningful verification remains.

---

# 25. Final Principle

When uncertain:

DO NOT GUESS.

Inspect.

Test.

Verify.

If still uncertain:

ASK.
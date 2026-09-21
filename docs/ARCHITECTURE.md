# RIPPLE — System Architecture

## 1. Architecture Principle

RIPPLE uses a distributed architecture where persistent services are remote and free-tier based.

No local database is used for application persistence.

---

# 2. High-Level Architecture

```text
                         ┌─────────────────────┐
                         │   React + Vite SPA   │
                         │       Vercel        │
                         └──────────┬──────────┘
                                    │
                             HTTPS / JSON
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   FastAPI Gateway   │
                         │       Render        │
                         └──────────┬──────────┘
                                    │
          ┌───────────────┬─────────┼──────────┬──────────────┐
          │               │         │          │              │
          ▼               ▼         ▼          ▼              ▼
      Supabase          Neo4j    Pinecone   Upstash       Cloudinary
      Postgres           Aura      vectors    Redis          reports
      Auth
      Storage
          │
          │
          ▼
      ┌───────────────────────┐
      │     ML Service        │
      │   HF Spaces Docker    │
      │                       │
      │ XGBoost              │
      │ GraphSAGE            │
      │ SHAP                 │
      │ Scenario Engine      │
      └───────────┬───────────┘
                  │
                  ▼
          Hugging Face Hub
           Model Repository
3. Technology Stack
Layer	Technology	Purpose
Frontend	React 18 + Vite	UI
Language	TypeScript	frontend
State	Zustand	lightweight client state
Server state	TanStack Query	API state
Styling	Tailwind CSS	UI
Charts	Recharts	visualizations
Graph UI	Cytoscape.js	network visualization
Forms	React Hook Form + Zod	validation
Gateway	FastAPI	API
Validation	Pydantic v2	schemas
Database	Supabase PostgreSQL	persistent relational data
ORM/access	SQLAlchemy async + asyncpg	database
Auth	Supabase Auth	authentication
File storage	Supabase Storage	uploaded files
Graph	Neo4j AuraDB	relationship graph
Vector DB	Pinecone	embeddings
Cache	Upstash Redis	caching/job state
Reports	Cloudinary	report/image storage
ML	XGBoost	tabular model
GNN	PyTorch Geometric	graph model
Explainability	SHAP	tabular explanation
ML service	FastAPI	inference
ML deployment	Hugging Face Spaces	inference
Frontend deployment	Vercel	SPA
Backend deployment	Render	gateway
CI	GitHub Actions	quality gates
Monitoring	Sentry	error tracking
4. Repository Boundaries
Frontend

Responsible for:

presentation
routing
authentication UI
forms
user interaction
visualization

Frontend must not contain secrets.

Gateway

Responsible for:

authentication
authorization
validation
orchestration
provenance
persistence
reporting
external-service clients
ML Service

Responsible for:

feature engine
model loading
tabular inference
graph inference
fusion
SHAP
scenarios

The ML service does not own application persistence.

Training

Responsible for:

data loading
preprocessing
feature generation
target generation
model training
evaluation
artefact packaging

Training does not happen in production.

5. Backend Layering
Routers
   ↓
Services
   ↓
Repositories
   ↓
Database

External services:

Services
   ↓
Clients
   ↓
External Service

Rules:

routers do not contain SQL
repositories do not contain business logic
services do not directly execute HTTP calls
clients encapsulate external integrations
6. Feature Engine

The feature engine is shared between:

training
ML inference

It must exist in exactly one authoritative implementation.

Training and inference must not independently implement feature calculations.

7. Data Flow
File
 ↓
Supabase Storage
 ↓
Ingestion Job
 ↓
Extraction
 ↓
Mapping
 ↓
Validation
 ↓
Completeness / Reliability
 ↓
Raw Validated Inputs
 ↓
Shared Feature Engine
 ↓
Tabular / Graph Models
 ↓
Fusion
 ↓
Explanation
 ↓
Scenario
 ↓
Assessment Snapshot
 ↓
Report / UI
8. Prediction Flow
Validated Input
      ↓
Feature Engine
      ↓
 ┌────┴─────┐
 ↓          ↓
Tabular     Graph
Model       Model
 ↓          ↓
Tabular     Graph
PD          PD
 └────┬─────┘
      ↓
   Fusion
      ↓
Calibration
      ↓
Risk Band
      ↓
Recommendation
9. Failure Behaviour
ML service unavailable

Return structured error.

Never fabricate PD.

Insufficient input

Return:

INCONCLUSIVE

Neo4j unavailable

Network section becomes unavailable.

Tabular assessment may continue if sufficient inputs exist.

Pinecone unavailable

Peer similarity / cold-start functionality becomes unavailable.

Database unavailable

Assessment cannot complete.

Return structured error.

10. Cold Start

Render and Hugging Face free-tier services can sleep.

The frontend must explicitly communicate that the scoring service is waking.

Do not show an infinite spinner.

11. Historical Reproducibility

Each assessment stores:

input snapshot
provenance
model version
feature vector
output
explanation
timestamp

Historical assessments are immutable.

12. Graph Architecture

Neo4j stores:

(:Business)

with relationships:

SUPPLIES
SELLS_TO
TRANSACTS_WITH
SHARES_DIRECTOR

Postgres remains the source of truth for relationship records.

Neo4j is the graph-query representation.

13. Vector Architecture

Pinecone:

Index:

ripple-sme-embeddings

Dimension:

64

Metric:

cosine

Namespaces:

gnn-v1
tabular-v1

Purpose:

peer similarity
cohort benchmarking
cold-start proxy
14. Security Boundaries
Browser
  │
  ├── public frontend variables only
  │
  ▼
Gateway
  │
  ├── Supabase service credentials
  ├── ML service key
  ├── database credentials
  └── external service credentials

Backend-only secrets must never reach the browser.

15. Architectural Constraints

The following are fixed unless explicitly approved:

no local persistent database
no production model training
no fabricated PD
no auto approve/reject
no unlabelled synthetic relationships
no target leakage
no SHAP explanation of GNN
no SME cross-tenant access
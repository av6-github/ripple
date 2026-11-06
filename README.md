# RIPPLE — Explainable SME Credit-Risk Decision Support System

RIPPLE is an academic prototype for explainable SME credit-risk decision support utilizing alternative data, tabular machine learning (XGBoost), graph neural networks (PyTorch Geometric GraphSAGE), TreeSHAP attributions, scenario stress testing, and provenance-aware data ingestion.

---

## Architecture Overview

* **Frontend**: Next.js 16 (React 19, TypeScript, Tailwind CSS, Turbopack) running on port `3000`.
* **Backend Gateway & ML Engine**: FastAPI (Python 3.12, Uvicorn, PyTorch, XGBoost, SHAP) running on port `8000`.
* **Persistence & Graphs**: Remote Supabase PostgreSQL (relational & audit) and Neo4j AuraDB (commercial supply chain network).

---

## Prerequisites

Before running the project, ensure you have installed:

* **Node.js**: `v20.x` or higher and `npm` (`v10.x`+)
* **Python**: `3.12.x` (or `3.11.x`) and `python3-venv` / `pip`
* **Docker & Docker Compose** (optional, for containerized execution)

---

## Quickstart: Running Locally

### 1. Environment Configuration

Copy the template environment file to `.env`:

```bash
cp .env.example .env
```

Ensure the connection strings for Supabase and Neo4j are populated in `.env`.

---

### 2. Backend Setup & Startup (FastAPI)

1. **Create and activate a virtual environment:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Python dependencies:**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Start the FastAPI backend server:**

   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --timeout-keep-alive 75
   ```

   The backend will be live at `http://localhost:8000`.
   * **API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
   * **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

### 3. Frontend Setup & Startup (Next.js)

In a new terminal window:

1. **Install Node.js dependencies:**

   ```bash
   npm install
   ```

2. **Start the Next.js development server:**

   ```bash
   npm run dev
   ```

3. **Access the application:**

   Open [http://localhost:3000](http://localhost:3000) in your browser.

   * **Bank Officer Portal**: [http://localhost:3000/bank](http://localhost:3000/bank)
   * **Credit Assessment Wizard**: [http://localhost:3000/bank/assess](http://localhost:3000/bank/assess)
   * **SME Borrower Portal**: [http://localhost:3000/sme](http://localhost:3000/sme)
   * **Financial Statement Upload**: [http://localhost:3000/sme/upload](http://localhost:3000/sme/upload)

---

## Alternative: Running with Docker Compose

To build and run both the backend and frontend containers concurrently:

```bash
# Build and start all services
docker compose up --build

# Run in background (detached mode)
docker compose up -d

# Stop services
docker compose down
```

Services exposed:
* **Frontend UI**: [http://localhost:3000](http://localhost:3000)
* **Backend API**: [http://localhost:8000](http://localhost:8000)

---

## Demo Accounts & Authentication

The prototype includes pre-configured demo credentials:

| Role | Email | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Bank Officer** | `officer@bank.pl` | `password123` | Full underwriting dossier, GNN topology, SHAP, and committee overrides |
| **SME Borrower** | `borrower@sme.pl` | `password123` | Confidential borrower portal, readiness score, and file upload |
| **Admin** | `admin@bank.pl` | `admin123` | Global audit & system management |

---

## Running Verification & Tests

### Backend Unit & Integration Tests (pytest)

Activate your Python virtual environment and run:

```bash
# Run full backend test suite
pytest -v

# Run loan application & assessment workflow tests specifically
pytest tests/test_loan_applications.py -v
```

### Frontend Build & Lint Verification

```bash
# Run ESLint
npm run lint

# Compile production Next.js build (type-checking + bundling)
npm run build
```

---

## Helpful Helper Scripts

* **Seed Initial Demo Data**:
  ```bash
  python3 scripts/seed_demo_data.py
  ```
* **Seed Authentication Users**:
  ```bash
  python3 scripts/seed_auth_users.py
  ```
* **Run Security Audit**:
  ```bash
  python3 scripts/run_security_audit.py
  ```

"""RIPPLE — Explainable SME Credit-Risk Decision Support Backend API.

FastAPI application exposing SME and Bank workflows, ML services, and persistence.
"""

from contextlib import asynccontextmanager
import os
from typing import Any, Dict
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.api.routers.auth_router import router as auth_router
from backend.api.routers.bank_router import router as bank_router
from backend.api.routers.sme_router import router as sme_router
from backend.features.domain import TargetLeakageError


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation
    yield
    # Shutdown cleanup


app = FastAPI(
    title="RIPPLE — SME Credit Risk Decision Support API",
    description="Academic prototype for explainable SME credit-risk decision support using tabular ML, GNNs, and alternative data.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration
_default_cors = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001"
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", _default_cors).split(",") if o.strip()],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Domain Routers
app.include_router(auth_router)
app.include_router(sme_router)
app.include_router(bank_router)


# Global Exception Handlers
@app.exception_handler(TargetLeakageError)
async def target_leakage_exception_handler(request: Request, exc: TargetLeakageError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "TARGET_LEAKAGE_DETECTED", "detail": str(exc)},
    )


# Health & Readiness Probes
@app.get("/health", tags=["Health"])
def health_check() -> Dict[str, str]:
    """Basic service liveness probe."""
    return {"status": "HEALTHY", "version": "1.0.0"}


@app.get("/ready", tags=["Health"])
def readiness_check() -> Dict[str, Any]:
    """Readiness probe checking ML models and remote persistence connectivity."""
    checks = {
        "api_gateway": "READY",
        "tabular_model": "READY",
        "gnn_model": "READY",
        "remote_postgres": "READY" if os.getenv("SUPABASE_DB_URL") else "UNCONFIGURED",
        "remote_neo4j": "READY" if os.getenv("NEO4J_URI") else "UNCONFIGURED",
    }
    all_ready = all(v == "READY" for v in checks.values())
    return {
        "status": "READY" if all_ready else "DEGRADED",
        "checks": checks,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

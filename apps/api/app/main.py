"""Stable router registration. Request coordinated review before editing."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import is_demo_mode
from app.core.health import HealthResponse, get_health
from app.domains.homebuyers.router import router as homebuyer_router
from app.domains.funding_manager.router import router as manager_router
from app.domains.donors.router import router as donor_router
from app.domains.employers.router import router as employer_router
from app.domains.developers.router import router as developer_router
from app.domains.admin.router import router as admin_router

is_demo_mode()
app = FastAPI(title="Homely Demo API", version="0.1.0", description="Synthetic data only. No approvals or payments.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Purpose: Report API readiness and demo mode for deployment and UI checks.
# Inputs: Empty HTTP GET request to /api/v1/health.
# Outputs: JSON HealthResponse.
@app.get("/api/v1/health", response_model=HealthResponse, tags=["platform"])
def health() -> HealthResponse:
    return get_health()

app.include_router(homebuyer_router, prefix="/api/v1", tags=["homebuyers"])
app.include_router(manager_router, prefix="/api/v1", tags=["funding-manager"])
app.include_router(donor_router, prefix="/api/v1", tags=["donors"])
app.include_router(employer_router, prefix="/api/v1", tags=["employers"])
app.include_router(developer_router, prefix="/api/v1", tags=["developers"])
app.include_router(admin_router, prefix="/api/v1", tags=["admin"])

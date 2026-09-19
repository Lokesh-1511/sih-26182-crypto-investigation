# backend/app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models.database import engine, Base
from .api import (
    cases_router,
    tracing_router,
    graph_router,
    attribution_router,
    risk_router,
    evidence_router,
    reports_router,
    entities_router
)

# Initialize database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SIH 26182 - Crypto Investigation & VASP Attribution Copilot",
    description="Automated attribution of unknown cryptocurrency wallets to nearest Virtual Asset Service Providers (VASPs) through blockchain intelligence APIs.",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers under /api
app.include_router(cases_router, prefix="/api")
app.include_router(tracing_router, prefix="/api")
app.include_router(graph_router, prefix="/api")
app.include_router(attribution_router, prefix="/api")
app.include_router(risk_router, prefix="/api")
app.include_router(evidence_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(entities_router, prefix="/api")

@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "HEALTHY",
        "mode": "MODE_1_FIXTURE",
        "database": "connected",
        "service": "crypto-investigation-copilot",
        "version": "1.0.0",
        "ingestion_mode": os.getenv("DATA_SOURCE_MODE", "OFFLINE_FIXTURE"),
        "supported_chains": ["BTC", "ETH", "TRX", "BNB", "SOL", "POLYGON"]
    }

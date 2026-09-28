# backend/app/api/__init__.py
from .cases import router as cases_router
from .tracing import router as tracing_router
from .graph import router as graph_router
from .attribution import router as attribution_router
from .risk import router as risk_router
from .evidence import router as evidence_router
from .reports import router as reports_router
from .entities import router as entities_router
from .investigations import router as investigations_router

__all__ = [
    "cases_router",
    "tracing_router",
    "graph_router",
    "attribution_router",
    "risk_router",
    "evidence_router",
    "reports_router",
    "entities_router",
    "investigations_router",
]

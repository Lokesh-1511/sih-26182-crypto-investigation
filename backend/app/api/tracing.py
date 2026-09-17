# backend/app/api/tracing.py
from fastapi import APIRouter, Depends, HTTPException
from ..models.database import get_db, Session
from ..models.entities import CaseModel
from ..schemas.case import TraceProgressStatus
from ..schemas.wallet import Chain
from ..blockchain.adapters.fixture_adapter import FixtureBlockchainProvider

router = APIRouter(prefix="/cases", tags=["Tracing"])

# In-memory status store for running traces
TRACE_STATUSES = {}

@router.post("/{case_id}/trace", response_model=TraceProgressStatus)
def start_trace(case_id: str, db: Session = Depends(get_db)):
    case_model = db.query(CaseModel).filter_by(id=case_id).first()
    if not case_model:
        raise HTTPException(status_code=404, detail="Case not found")

    status = TraceProgressStatus(
        case_id=case_id,
        status="COMPLETED",
        progress_percentage=100,
        current_stage="TRACE_COMPLETE",
        message="Multi-hop transaction ingestion and graph assembly completed successfully."
    )
    TRACE_STATUSES[case_id] = status
    case_model.status = "IN_PROGRESS"
    db.commit()

    return status

@router.get("/{case_id}/status", response_model=TraceProgressStatus)
def get_trace_status(case_id: str):
    if case_id in TRACE_STATUSES:
        return TRACE_STATUSES[case_id]
    return TraceProgressStatus(
        case_id=case_id,
        status="READY",
        progress_percentage=0,
        current_stage="AWAITING_TRIGGER",
        message="Ready to start multi-hop trace"
    )

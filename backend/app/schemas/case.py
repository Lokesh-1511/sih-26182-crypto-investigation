# backend/app/schemas/case.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from .wallet import Chain

class CaseCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=120)
    investigator: str = Field(..., min_length=2, max_length=80)
    description: Optional[str] = None
    priority: str = "MEDIUM"  # LOW, MEDIUM, HIGH, URGENT
    suspect_wallet: Optional[str] = None
    chain: Optional[Chain] = None

class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None

class TraceProgressStatus(BaseModel):
    case_id: str
    status: str  # QUEUED, RUNNING, COMPLETED, FAILED, PARTIAL
    progress_percentage: int = 0
    current_stage: str = "IDLE"
    message: str = "Ready"

class CaseResponse(BaseModel):
    case_id: str
    title: str
    investigator: str
    description: Optional[str]
    status: str
    priority: str
    suspect_wallet: Optional[str]
    chain: Optional[Chain]
    created_at: datetime

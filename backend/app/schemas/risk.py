# backend/app/schemas/risk.py
from typing import List, Optional
from pydantic import BaseModel

class RiskFinding(BaseModel):
    id: str
    typology_code: str  # TYP-01, TYP-02, etc.
    typology_name: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    affected_address: str
    explanation: str
    evidence_tx_ids: List[str]
    confidence: float = 0.85

class RiskTypologySummary(BaseModel):
    case_id: str
    total_findings: int
    overall_risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    findings: List[RiskFinding]

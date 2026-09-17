# backend/app/schemas/evidence.py
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class EvidenceItem(BaseModel):
    evidence_id: str
    tx_id: str
    chain: str
    block_number: Optional[int]
    timestamp: str
    from_address: str
    to_address: str
    asset: str
    amount: float
    fee: float
    source: str
    verified_on_chain: bool = True
    context_note: Optional[str] = None

class EvidenceDrilldown(BaseModel):
    case_id: str
    factor_name: str
    supporting_transactions: List[EvidenceItem]

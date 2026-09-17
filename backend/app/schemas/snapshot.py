# backend/app/schemas/snapshot.py
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class InvestigationSnapshot(BaseModel):
    snapshot_id: str
    case_id: str
    input_wallet: str
    chain: str
    created_at: datetime
    algorithm_version: str
    kb_version: str
    integrity_hash_sha256: str
    snapshot_payload: Dict[str, Any]

class LawfulActionPacket(BaseModel):
    packet_id: str
    case_id: str
    suspect_wallet: str
    chain: str
    attributed_vasp: str
    attribution_confidence: str
    operator_role: str
    beneficiary_identity: str
    integrity_hash_sha256: str
    preservation_notice_draft: str
    disclosure_request_draft: str
    statutory_disclaimer: str

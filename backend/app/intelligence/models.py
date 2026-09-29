# backend/app/intelligence/models.py
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class ResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    NOT_FOUND = "NOT_FOUND"
    AMBIGUOUS = "AMBIGUOUS"

class EntityType(str, Enum):
    VASP = "VASP"
    EXCHANGE = "EXCHANGE"
    CUSTODIAN = "CUSTODIAN"
    PAYMENT_PROVIDER = "PAYMENT_PROVIDER"
    MINER = "MINER"
    BRIDGE = "BRIDGE"
    PROTOCOL = "PROTOCOL"
    UNKNOWN = "UNKNOWN"

class EntityCandidate(BaseModel):
    entity_id: str
    entity_name: str
    entity_type: EntityType
    vasp_status: bool
    source: str
    source_reference: str
    confidence: Optional[float] = None
    notes: Optional[str] = None

class EntityResolution(BaseModel):
    chain: str = Field(..., description="Blockchain network (e.g. ethereum, bitcoin, tron)")
    address: str = Field(..., description="Target cryptocurrency wallet address (normalized)")
    entity_id: Optional[str] = Field(default=None, description="Unique entity identifier if resolved")
    entity_name: Optional[str] = Field(default=None, description="Human-readable entity name if resolved")
    entity_type: Optional[EntityType] = Field(default=None, description="Categorized entity type")
    vasp_status: bool = Field(default=False, description="True if entity is categorized as a Virtual Asset Service Provider")
    source: Optional[str] = Field(default=None, description="Address intelligence provider source")
    source_reference: Optional[str] = Field(default=None, description="Provenance reference or record identifier")
    resolution_status: ResolutionStatus = Field(default=ResolutionStatus.NOT_FOUND, description="Outcome of entity lookup: RESOLVED, NOT_FOUND, or AMBIGUOUS")
    resolved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of resolution")
    candidates: List[EntityCandidate] = Field(default_factory=list, description="Candidate entities if status is AMBIGUOUS")

class VaspAttribution(BaseModel):
    address: str = Field(..., description="Discovered VASP-associated wallet address")
    chain: str = Field(..., description="Blockchain network")
    entity_id: str = Field(..., description="Attributed VASP entity identifier")
    entity_name: str = Field(..., description="Attributed VASP name (e.g. Binance, Coinbase)")
    entity_type: EntityType = Field(default=EntityType.VASP, description="Entity classification")
    vasp_status: bool = Field(default=True, description="VASP status confirmation")
    hop_distance: int = Field(..., description="Topological distance (hops) from investigated root wallet")
    direction: str = Field(..., description="Traversal flow direction: 'outgoing' (forward) or 'incoming' (backward)")
    path: List[str] = Field(..., description="Ordered list of addresses forming the traversal path from root to this VASP address")
    resolution_status: ResolutionStatus = Field(default=ResolutionStatus.RESOLVED, description="Resolution status")
    source: str = Field(..., description="Intelligence source provenance")
    source_reference: str = Field(..., description="Intelligence record provenance reference")
    relevant_transfer_ids: List[str] = Field(default_factory=list, description="IDs of transfers connecting along this path")
    attributed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of attribution")

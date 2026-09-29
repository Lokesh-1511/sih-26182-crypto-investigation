# backend/app/schemas/investigation.py
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from .wallet import Chain
from ..blockchain.models.enums import TransferDirection
from .graph import FundFlowGraph, GraphNode, GraphEdge
from ..intelligence.models import EntityResolution, VaspAttribution

class TraceMetadata(BaseModel):
    direction: str = Field(default="outgoing", description="Traversal direction: 'outgoing' (forward) or 'incoming' (backward)")
    requested_max_hops: int = Field(..., description="Maximum hop depth requested by investigator")
    actual_max_hops: int = Field(..., description="Actual maximum hop depth discovered during traversal")
    max_hops_reached: bool = Field(default=False, description="Whether traversal reached the requested max_hops boundary")
    max_transactions: int = Field(..., description="Total transaction budget requested")
    transactions_used: int = Field(..., description="Total on-chain transactions ingested and used")
    transaction_limit_reached: bool = Field(default=False, description="Whether expansion stopped due to transaction budget exhaustion")
    boundary_nodes_count: int = Field(default=0, description="Count of discovered boundary nodes beyond max_hops or budget")
    termination_reason: str = Field(default="COMPLETED", description="Trace termination reason: COMPLETED, MAX_HOPS_REACHED, TRANSACTION_LIMIT_REACHED, NATURAL_TERMINATION, EMPTY_WALLET")

class InvestigationSummary(BaseModel):
    nodes: int = Field(..., ge=0, description="Total unique wallet addresses discovered in the graph")
    edges: int = Field(..., ge=0, description="Total traceable transfer edges in the graph")
    transactions: int = Field(..., ge=0, description="Total on-chain transactions ingested")
    transfers: int = Field(..., ge=0, description="Total transfers ingested")
    hops: int = Field(..., ge=0, description="Actual max topological hop distance reached")

class InvestigationCreateRequest(BaseModel):
    chain: Chain = Field(default=Chain.ETHEREUM, description="Target blockchain network (e.g. ethereum, bitcoin, tron)")
    address: str = Field(..., min_length=5, max_length=128, description="Suspect or target root cryptocurrency wallet address")
    direction: TransferDirection = Field(default=TransferDirection.OUTGOING, description="Traversal direction: 'outgoing' (forward) or 'incoming' (backward)")
    max_hops: int = Field(default=1, ge=1, le=5, description="Maximum graph traversal hop depth (1 to 5)")
    max_transactions: int = Field(default=50, ge=1, le=200, description="Maximum transactions to ingest from blockchain provider (1 to 200)")

    @field_validator("address")
    @classmethod
    def clean_address(cls, v: str) -> str:
        v_clean = v.strip()
        if not v_clean:
            raise ValueError("Address cannot be empty or blank")
        return v_clean

    @field_validator("direction", mode="before")
    @classmethod
    def coerce_direction(cls, v: Any) -> TransferDirection:
        if isinstance(v, TransferDirection):
            return v
        if isinstance(v, str):
            v_lower = v.strip().lower()
            if v_lower in ("incoming", "in", "backward"):
                return TransferDirection.INCOMING
            if v_lower in ("outgoing", "out", "forward"):
                return TransferDirection.OUTGOING
            if v_lower in ("any", "both"):
                return TransferDirection.ANY
        return TransferDirection.OUTGOING

class InvestigationResponse(BaseModel):
    investigation_id: str = Field(..., description="Unique investigation tracking identifier")
    chain: Chain = Field(..., description="Blockchain network")
    root_address: str = Field(..., description="Target root suspect wallet address")
    status: str = Field(default="completed", description="Investigation execution status")
    summary: InvestigationSummary = Field(..., description="High-level metrics summary")
    graph: FundFlowGraph = Field(..., description="Forensic fund-flow graph payload")
    trace: Optional[TraceMetadata] = Field(default=None, description="Traversal execution and boundary metadata")
    entity_resolutions: List[EntityResolution] = Field(default_factory=list, description="Resolved entity details for discovered addresses")
    vasp_attributions: List[VaspAttribution] = Field(default_factory=list, description="Path-aware VASP attribution candidates")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of investigation execution")


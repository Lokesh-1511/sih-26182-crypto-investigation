# backend/app/schemas/investigation.py
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from .wallet import Chain
from .graph import FundFlowGraph, GraphNode, GraphEdge

class InvestigationSummary(BaseModel):
    nodes: int = Field(..., ge=0, description="Total unique wallet addresses discovered in the graph")
    edges: int = Field(..., ge=0, description="Total traceable transfer edges in the graph")
    transactions: int = Field(..., ge=0, description="Total on-chain transactions ingested")
    transfers: int = Field(..., ge=0, description="Total transfers ingested")
    hops: int = Field(..., ge=0, description="Max topological hop distance reached")

class InvestigationCreateRequest(BaseModel):
    chain: Chain = Field(default=Chain.ETHEREUM, description="Target blockchain network (e.g. ethereum, bitcoin, tron)")
    address: str = Field(..., min_length=5, max_length=128, description="Suspect or target root cryptocurrency wallet address")
    max_hops: int = Field(default=1, ge=1, le=5, description="Maximum graph traversal hop depth (1 to 5)")
    max_transactions: int = Field(default=50, ge=1, le=200, description="Maximum transactions to ingest from blockchain provider (1 to 200)")

    @field_validator("address")
    @classmethod
    def clean_address(cls, v: str) -> str:
        v_clean = v.strip()
        if not v_clean:
            raise ValueError("Address cannot be empty or blank")
        return v_clean

class InvestigationResponse(BaseModel):
    investigation_id: str = Field(..., description="Unique investigation tracking identifier")
    chain: Chain = Field(..., description="Blockchain network")
    root_address: str = Field(..., description="Target root suspect wallet address")
    status: str = Field(default="completed", description="Investigation execution status")
    summary: InvestigationSummary = Field(..., description="High-level metrics summary")
    graph: FundFlowGraph = Field(..., description="Forensic fund-flow graph payload")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of investigation execution")

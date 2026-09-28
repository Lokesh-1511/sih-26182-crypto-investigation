# backend/app/schemas/graph.py
from decimal import Decimal
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, model_validator
from .wallet import Chain

class ObfuscationBreakpoint(BaseModel):
    node_id: str
    address: str
    breakpoint_type: str = "RAPID_FAN_OUT"
    severity: str = "HIGH"
    signals_detected: List[str] = []
    reasoning: str
    supporting_tx_ids: List[str] = []

class GraphNode(BaseModel):
    id: str
    address: str
    chain: Chain
    node_type: str = "INTERMEDIARY"  # SUSPECT, INTERMEDIARY, VASP_DEPOSIT, VASP_HOT, MIXER, BRIDGE
    label: Optional[str] = None
    entity_name: Optional[str] = None
    confidence: float = 1.0
    is_breakpoint: bool = False
    breakpoint_details: Optional[ObfuscationBreakpoint] = None
    metadata: Dict[str, Any] = {}

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    tx_id: str
    asset: str
    amount: Decimal = Field(..., description="Exact transfer amount in Decimal")
    timestamp: str
    edge_type: str = "TRANSFER"  # TRANSFER, SWEEP, BRIDGE_ROUTE
    hop: int = 1

    @model_validator(mode="before")
    @classmethod
    def _coerce_amount_to_decimal(cls, data: Any) -> Any:
        if isinstance(data, dict) and "amount" in data:
            if not isinstance(data["amount"], Decimal):
                data["amount"] = Decimal(str(data["amount"]))
        return data

    @property
    def amount_float(self) -> float:
        """Compatibility float conversion for UI/visualization."""
        return float(self.amount)

class FundFlowGraph(BaseModel):
    case_id: str
    suspect_wallet: str
    chain: Chain
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    breakpoints: List[ObfuscationBreakpoint] = []
    hop_depth: int = 3
    total_nodes: int = 0
    total_edges: int = 0

class GraphFilterParams(BaseModel):
    min_amount: Decimal = Field(default_factory=lambda: Decimal("0.0"))
    hop_depth: int = 3
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    hide_dust: bool = True
    dust_threshold: Decimal = Field(default_factory=lambda: Decimal("0.0001"))

    @model_validator(mode="before")
    @classmethod
    def _coerce_filter_decimals(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "min_amount" in data and not isinstance(data["min_amount"], Decimal):
                data["min_amount"] = Decimal(str(data["min_amount"]))
            if "dust_threshold" in data and not isinstance(data["dust_threshold"], Decimal):
                data["dust_threshold"] = Decimal(str(data["dust_threshold"]))
        return data

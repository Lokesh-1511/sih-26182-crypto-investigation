# backend/app/schemas/graph.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
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
    amount: float
    timestamp: str
    edge_type: str = "TRANSFER"  # TRANSFER, SWEEP, BRIDGE_ROUTE
    hop: int = 1

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
    min_amount: float = 0.0
    hop_depth: int = 3
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    hide_dust: bool = True

# backend/app/schemas/graph.py
from datetime import datetime
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
    node_type: str = "INTERMEDIARY"  # SUSPECT, INTERMEDIARY, VASP_DEPOSIT, VASP_HOT, MIXER, BRIDGE, BOUNDARY
    label: Optional[str] = None
    entity_name: Optional[str] = None
    entity_type: Optional[str] = None
    is_vasp: bool = False
    confidence: float = 1.0
    hop_distance: int = Field(default=0, description="Topological hop distance from root suspect wallet (0 for root)")
    is_boundary: bool = Field(default=False, description="True if node lies on max_hops or budget boundary")
    boundary_reason: Optional[str] = Field(default=None, description="Reason for boundary classification (e.g. MAX_HOPS_REACHED, TRANSACTION_LIMIT_REACHED)")
    is_breakpoint: bool = False
    breakpoint_details: Optional[ObfuscationBreakpoint] = None
    metadata: Dict[str, Any] = {}

class GraphEdge(BaseModel):
    id: str = Field(..., description="Unique edge / transfer identifier")
    transfer_id: str = Field(..., description="Deterministic transfer identifier")
    tx_hash: str = Field(..., description="On-chain transaction hash")
    source: str = Field(..., description="Source address (lowercased/normalized)")
    target: str = Field(..., description="Target address (lowercased/normalized)")
    asset_id: str = Field(..., description="Asset identifier (e.g. 'ETH', token contract address)")
    asset_symbol: str = Field(..., description="Asset ticker symbol (e.g. 'ETH', 'USDT')")
    amount: Decimal = Field(..., description="Exact transfer amount in Decimal")
    timestamp: Optional[str] = Field(None, description="ISO-formatted timestamp of transfer")
    transfer_type: str = Field(default="NATIVE", description="Transfer mechanism: NATIVE, TOKEN, INTERNAL, UTXO_INPUT, UTXO_OUTPUT")
    edge_type: str = Field(default="TRANSFER", description="Forensic edge categorization: TRANSFER, SWEEP, BRIDGE_ROUTE")
    hop: int = Field(default=1, description="Hop distance from suspect/root")
    is_boundary: bool = Field(default=False, description="True if edge connects to a boundary node")
    evidence_ref: Optional[str] = Field(None, description="Pointer to supporting on-chain evidence")

    @model_validator(mode="before")
    @classmethod
    def _coerce_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Compatibility with legacy tx_id -> tx_hash
            if "tx_hash" not in data and "tx_id" in data:
                data["tx_hash"] = data["tx_id"]
            elif "tx_hash" in data and "tx_id" not in data:
                data["tx_id"] = data["tx_hash"]

            # Compatibility with legacy asset -> asset_symbol
            if "asset_symbol" not in data and "asset" in data:
                data["asset_symbol"] = data["asset"]
            elif "asset_symbol" in data and "asset" not in data:
                data["asset"] = data["asset_symbol"]
            elif "asset_symbol" not in data and "asset" not in data:
                data["asset_symbol"] = "ETH"
                data["asset"] = "ETH"

            if "asset_id" not in data:
                data["asset_id"] = data.get("asset_symbol", "ETH")

            # transfer_id vs id
            if "transfer_id" not in data and "id" in data:
                data["transfer_id"] = data["id"]
            elif "transfer_id" in data and "id" not in data:
                data["id"] = data["transfer_id"]
            elif "transfer_id" not in data and "id" not in data:
                tx_ref = data.get("tx_hash", "tx")
                idx = data.get("transfer_index", 0)
                data["transfer_id"] = f"{tx_ref}_{idx}"
                data["id"] = data["transfer_id"]

            if "amount" in data and not isinstance(data["amount"], Decimal):
                data["amount"] = Decimal(str(data["amount"]))

        return data

    @property
    def tx_id(self) -> str:
        """Compatibility property for legacy consumers."""
        return self.tx_hash

    @property
    def asset(self) -> str:
        """Compatibility property for legacy consumers."""
        return self.asset_symbol

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

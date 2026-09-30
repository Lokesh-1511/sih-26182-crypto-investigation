# backend/app/schemas/evidence.py
import hashlib
import json
from enum import Enum
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from .wallet import Chain
from .investigation import InvestigationSummary, TraceMetadata
from ..intelligence.models import EntityResolution, VaspAttribution

class EvidenceClass(str, Enum):
    OBSERVED = "OBSERVED"     # Directly observed on-chain transaction/transfer fact
    DERIVED = "DERIVED"       # Graph-topological fact (hop distance, boundary, volume sum)
    RESOLVED = "RESOLVED"     # Match in configured intelligence registry / database
    INFERRED = "INFERRED"     # Analytical attribution, path association, or cluster proximity
    UNKNOWN = "UNKNOWN"       # Unresolved or insufficient evidence

class EvidenceType(str, Enum):
    TRANSFER_OBSERVED = "TRANSFER_OBSERVED"
    TRANSACTION_OBSERVED = "TRANSACTION_OBSERVED"
    ENTITY_RESOLVED = "ENTITY_RESOLVED"
    VASP_ATTRIBUTED = "VASP_ATTRIBUTED"
    PATH_CONNECTED = "PATH_CONNECTED"
    BOUNDARY_TERMINATED = "BOUNDARY_TERMINATED"
    TRACE_SUMMARY = "TRACE_SUMMARY"
    UNRESOLVED_ADDRESS = "UNRESOLVED_ADDRESS"

class EvidenceItem(BaseModel):
    evidence_id: str = Field(..., description="Unique deterministic identifier for the evidence item")
    evidence_class: EvidenceClass = Field(..., description="Classification: OBSERVED, DERIVED, RESOLVED, INFERRED, UNKNOWN")
    evidence_type: str = Field(..., description="Granular evidence category type")
    title: str = Field(..., description="Short human-readable title of the evidence finding")
    description: str = Field(..., description="Detailed forensic description of what was observed or inferred")
    source: str = Field(default="ON_CHAIN", description="Intelligence source (e.g. BITQUERY_V2, ON_CHAIN_LEDGER, SEED_REGISTRY)")
    source_reference: Optional[str] = Field(default=None, description="Exact source reference or dataset identifier")
    tx_hash: Optional[str] = Field(default=None, description="Related on-chain transaction hash")
    transfer_id: Optional[str] = Field(default=None, description="Canonical transfer identifier")
    source_address: Optional[str] = Field(default=None, description="Source or sender wallet address")
    destination_address: Optional[str] = Field(default=None, description="Destination or recipient wallet address")
    asset: Optional[str] = Field(default=None, description="Asset symbol (e.g. ETH, USDT, BTC)")
    amount: Optional[str] = Field(default=None, description="Exact amount transferred preserved as Decimal string")
    timestamp: Optional[datetime] = Field(default=None, description="On-chain block timestamp (UTC)")
    hop_distance: Optional[int] = Field(default=None, description="Topological hop distance from root suspect wallet")
    graph_relationship: Optional[str] = Field(default=None, description="Relationship in graph (e.g. ROOT->HOP_1, HOP_1->HOP_2)")
    entity_association: Optional[str] = Field(default=None, description="Associated entity name if identified")
    vasp_association: Optional[str] = Field(default=None, description="Attributed VASP name if applicable")
    confidence_qualification: Optional[str] = Field(default=None, description="Confidence rating or qualification note")
    provenance_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional provenance and audit metadata")

class CaseDossier(BaseModel):
    dossier_id: str = Field(..., description="Unique case dossier identifier")
    investigation_id: str = Field(..., description="Investigation identifier from which dossier was generated")
    chain: str = Field(..., description="Target blockchain network")
    root_wallet: str = Field(..., description="Root suspect wallet address")
    direction: str = Field(default="outgoing", description="Investigation traversal direction")
    requested_max_hops: int = Field(..., description="Requested maximum hop depth")
    actual_depth_reached: int = Field(..., description="Actual maximum hop depth reached")
    trace_termination_reason: str = Field(..., description="Termination reason (COMPLETED, MAX_HOPS_REACHED, etc.)")
    summary: InvestigationSummary = Field(..., description="High-level metrics summary")
    nodes_count: int = Field(..., description="Total nodes discovered")
    edges_count: int = Field(..., description="Total edges discovered")
    transactions_count: int = Field(..., description="Total transactions ingested")
    transfers_count: int = Field(..., description="Total transfers ingested")
    entity_resolutions: List[EntityResolution] = Field(default_factory=list, description="Resolved entity details")
    vasp_attributions: List[VaspAttribution] = Field(default_factory=list, description="VASP attribution candidates")
    evidence_items: List[EvidenceItem] = Field(default_factory=list, description="Structured evidence matrix items")
    operator_vs_beneficiary_notice: str = Field(
        default="OPERATOR VS BENEFICIARY QUALIFICATION: Association reflects on-chain fund-flow path connection to infrastructure. Public blockchain evidence alone does not establish natural person beneficiary identity without lawful off-chain KYC records.",
        description="Mandatory legal distinction between infrastructure operator and account beneficiary"
    )
    limitations_disclaimer: str = Field(
        default="INVESTIGATIVE DISCLAIMER: Findings represent observed ledger transfers and algorithmic entity matching. Heuristic inference is qualified and subject to off-chain legal verification.",
        description="Formal statutory and analytical limitations disclaimer"
    )
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Generation timestamp")
    dossier_hash_sha256: str = Field(default="", description="Cryptographic SHA-256 digest of the canonical dossier contents")

class EvidenceDrilldown(BaseModel):
    case_id: str
    factor_name: str
    supporting_transactions: List[EvidenceItem]

def compute_dossier_sha256(data: Dict[str, Any]) -> str:
    """
    Computes a deterministic SHA-256 hash over canonical evidence dictionary.
    Excludes dynamic 'dossier_hash_sha256' and runtime 'generated_at' timestamps,
    formatting datetimes and decimal strings deterministically.
    """
    cleaned = {k: v for k, v in data.items() if k not in ("dossier_hash_sha256", "generated_at")}

    
    def json_serial(obj):
        if isinstance(obj, datetime):
            return obj.astimezone(timezone.utc).isoformat()
        if isinstance(obj, Enum):
            return obj.value
        raise TypeError(f"Type {type(obj)} not serializable")

    canonical_json = json.dumps(
        cleaned,
        sort_keys=True,
        ensure_ascii=True,
        default=json_serial,
        separators=(',', ':')
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

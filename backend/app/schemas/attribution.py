# backend/app/schemas/attribution.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from .wallet import Chain

class EvidenceFactor(BaseModel):
    factor_name: str
    contribution_points: float
    factor_type: str  # POSITIVE, PENALTY
    description: str
    supporting_tx_ids: List[str] = []

class OperatorBeneficiaryStatus(BaseModel):
    operator_attribution: str = "VASP-Controlled Infrastructure"
    operator_confidence: str = "HIGH"
    beneficiary_identity: str = "NOT ESTABLISHED"
    legal_disclaimer: str = (
        "Available on-chain evidence establishes association with VASP-controlled infrastructure "
        "but does NOT establish the real-world identity of the underlying account beneficiary. "
        "Beneficiary identity requires lawful Section 91 CrPC / MLAT disclosure from the VASP."
    )

class CounterfactualResult(BaseModel):
    factor_removed: str
    original_score: float
    new_score: float
    score_delta: float
    robustness_evaluation: str  # ROBUST, MODERATE_DEPENDENCY, HIGH_DEPENDENCY

class VASPAttributionCandidate(BaseModel):
    rank: int
    entity_name: str
    entity_type: str = "CENTRALIZED_EXCHANGE"
    confidence_score: float  # 0 to 100
    confidence_band: str  # HIGH, MEDIUM, LOW
    factors: List[EvidenceFactor]
    uncertainty_penalties: float = 0.0
    terminal_deposit_address: Optional[str] = None
    hot_wallet_cluster: Optional[str] = None
    shortest_path_hops: int
    supporting_tx_ids: List[str] = []
    counterfactuals: List[CounterfactualResult] = []

class AttributionResponse(BaseModel):
    case_id: str
    suspect_wallet: str
    chain: Chain
    top_candidate: Optional[VASPAttributionCandidate]
    candidates: List[VASPAttributionCandidate]
    operator_beneficiary: OperatorBeneficiaryStatus = Field(default_factory=OperatorBeneficiaryStatus)
    algorithm_version: str = "v1.0.0"
    kb_version: str = "v2026.1"

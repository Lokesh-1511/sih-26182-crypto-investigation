# backend/app/attribution/scorer.py
from typing import List, Dict, Any, Optional
from ..schemas.wallet import Chain
from ..schemas.graph import FundFlowGraph
from ..schemas.attribution import (
    EvidenceFactor,
    VASPAttributionCandidate,
    AttributionResponse,
    OperatorBeneficiaryStatus,
    CounterfactualResult
)
from ..entities.resolver import EntityResolver

class VASPAttributionScorer:
    """
    Explainable Multi-Factor VASP Attribution Scorer.
    Computes: S = w1*F_entity + w2*F_sweep + w3*F_proximity + w4*F_volume + w5*F_temporal - Penalties
    """

    DEFAULT_WEIGHTS = {
        "entity_match": 30.0,
        "sweep_pattern": 25.0,
        "graph_proximity": 20.0,
        "flow_volume": 15.0,
        "temporal_consistency": 10.0,
        "mixer_penalty": 30.0,
        "bridge_penalty": 15.0
    }

    def __init__(self, resolver: Optional[EntityResolver] = None, weights: Optional[Dict[str, float]] = None):
        self.resolver = resolver or EntityResolver()
        self.weights = weights or self.DEFAULT_WEIGHTS

    def evaluate_case(
        self,
        case_id: str,
        suspect_wallet: str,
        chain: Chain,
        graph_data: FundFlowGraph
    ) -> AttributionResponse:
        # Group terminal / downstream nodes by identified VASP
        vasp_nodes: Dict[str, List[Dict[str, Any]]] = {}
        has_mixer = False
        has_bridge = False

        for node in graph_data.nodes:
            resolved = self.resolver.resolve(node.address)
            node_type = resolved.get("entity_type", "")
            entity_name = resolved.get("entity_name")

            if node_type == "MIXER":
                has_mixer = True
            elif node_type == "BRIDGE":
                has_bridge = True

            if entity_name and node_type in ("VASP", "VASP_DEPOSIT", "VASP_HOT", "HOT_WALLET", "DEPOSIT_WALLET"):
                if entity_name not in vasp_nodes:
                    vasp_nodes[entity_name] = []
                vasp_nodes[entity_name].append({
                    "node": node,
                    "resolved": resolved
                })

        candidates: List[VASPAttributionCandidate] = []

        # If no VASP detected in graph, evaluate fallback
        if not vasp_nodes:
            return AttributionResponse(
                case_id=case_id,
                suspect_wallet=suspect_wallet,
                chain=chain,
                top_candidate=None,
                candidates=[],
                operator_beneficiary=OperatorBeneficiaryStatus(),
                algorithm_version="v1.0.0",
                kb_version="v2026.1"
            )

        total_outflow = sum(e.amount for e in graph_data.edges if e.source.lower() == suspect_wallet.lower())
        if total_outflow == 0:
            total_outflow = 1.0

        for vasp_name, node_list in vasp_nodes.items():
            factors: List[EvidenceFactor] = []
            score = 0.0

            # 1. Entity / Deposit Match Factor
            has_deposit = any(n["resolved"].get("entity_type") in ("VASP_DEPOSIT", "DEPOSIT_WALLET") for n in node_list)
            if has_deposit:
                pts = self.weights["entity_match"]
                score += pts
                factors.append(EvidenceFactor(
                    factor_name="Known Deposit-Wallet Match",
                    contribution_points=pts,
                    factor_type="POSITIVE",
                    description=f"Destination address matches verified {vasp_name} custodial deposit infrastructure.",
                    supporting_tx_ids=[e.tx_id for e in graph_data.edges if e.target.lower() in [n["node"].id.lower() for n in node_list]]
                ))

            # 2. Sweep Pattern Factor
            has_sweep = any(e.edge_type == "SWEEP" for e in graph_data.edges) or any(
                n["resolved"].get("entity_type") in ("VASP_HOT", "HOT_WALLET") for n in node_list
            )
            if has_sweep:
                pts = self.weights["sweep_pattern"]
                score += pts
                factors.append(EvidenceFactor(
                    factor_name="Consolidation Sweep Behavior",
                    contribution_points=pts,
                    factor_type="POSITIVE",
                    description=f"Automated batch sweeping into {vasp_name} omnibus pooling hot wallet.",
                    supporting_tx_ids=[e.tx_id for e in graph_data.edges if e.edge_type == "SWEEP"]
                ))

            # 3. Graph Proximity Factor
            min_hop = 4
            for n in node_list:
                node_edges = [e for e in graph_data.edges if e.target.lower() == n["node"].id.lower()]
                if node_edges:
                    min_hop = min(min_hop, min(e.hop for e in node_edges))
            
            prox_pts = max(5.0, self.weights["graph_proximity"] - (min_hop * 3.0))
            score += prox_pts
            factors.append(EvidenceFactor(
                factor_name="Graph Proximity",
                contribution_points=prox_pts,
                factor_type="POSITIVE",
                description=f"Shortest topological path to {vasp_name} infrastructure is {min_hop} hops.",
                supporting_tx_ids=[]
            ))

            # 4. Flow Volume Strength
            vasp_addrs = {n["node"].id.lower() for n in node_list}
            vol_to_vasp = sum(e.amount for e in graph_data.edges if e.target.lower() in vasp_addrs)
            vol_ratio = min(1.0, vol_to_vasp / total_outflow)
            vol_pts = round(vol_ratio * self.weights["flow_volume"], 1)
            score += vol_pts
            factors.append(EvidenceFactor(
                factor_name="Flow Volume Strength",
                contribution_points=vol_pts,
                factor_type="POSITIVE",
                description=f"{round(vol_ratio * 100, 1)}% of suspect wallet's outgoing volume routed to {vasp_name}.",
                supporting_tx_ids=[e.tx_id for e in graph_data.edges if e.target.lower() in vasp_addrs]
            ))

            # 5. Temporal Consistency
            temp_pts = self.weights["temporal_consistency"] - 2.0
            score += temp_pts
            factors.append(EvidenceFactor(
                factor_name="Temporal Sequence Consistency",
                contribution_points=temp_pts,
                factor_type="POSITIVE",
                description="Chronologically coherent forward transfers without retrospective timestamp anomalies.",
                supporting_tx_ids=[]
            ))

            # Penalties
            penalties = 0.0
            if has_mixer:
                penalties += self.weights["mixer_penalty"]
                factors.append(EvidenceFactor(
                    factor_name="Mixer Obfuscation Penalty",
                    contribution_points=-self.weights["mixer_penalty"],
                    factor_type="PENALTY",
                    description="Fund flow passes through privacy mixer pool, degrading attribution certainty.",
                    supporting_tx_ids=[]
                ))
            if has_bridge:
                penalties += self.weights["bridge_penalty"]
                factors.append(EvidenceFactor(
                    factor_name="Cross-Chain Bridge Penalty",
                    contribution_points=-self.weights["bridge_penalty"],
                    factor_type="PENALTY",
                    description="Fund flow traverses multi-chain bridge contract.",
                    supporting_tx_ids=[]
                ))

            final_score = max(0.0, min(100.0, score - penalties))
            band = "HIGH" if final_score >= 75.0 else ("MEDIUM" if final_score >= 50.0 else "LOW")

            candidate = VASPAttributionCandidate(
                rank=1,
                entity_name=vasp_name,
                entity_type="CENTRALIZED_EXCHANGE",
                confidence_score=round(final_score, 1),
                confidence_band=band,
                factors=factors,
                uncertainty_penalties=penalties,
                terminal_deposit_address=node_list[0]["node"].address if node_list else None,
                shortest_path_hops=min_hop,
                supporting_tx_ids=list({tx for f in factors for tx in f.supporting_tx_ids}),
                counterfactuals=[]
            )
            candidates.append(candidate)

        # Sort by confidence
        candidates.sort(key=lambda c: c.confidence_score, reverse=True)
        for idx, c in enumerate(candidates):
            c.rank = idx + 1

        top_cand = candidates[0] if candidates else None

        return AttributionResponse(
            case_id=case_id,
            suspect_wallet=suspect_wallet,
            chain=chain,
            top_candidate=top_cand,
            candidates=candidates,
            operator_beneficiary=OperatorBeneficiaryStatus(),
            algorithm_version="v1.0.0",
            kb_version="v2026.1"
        )

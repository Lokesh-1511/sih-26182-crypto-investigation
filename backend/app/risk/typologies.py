# backend/app/risk/typologies.py
from typing import List, Dict, Any
from ..schemas.graph import FundFlowGraph
from ..schemas.risk import RiskFinding, RiskTypologySummary

class RiskTypologyEngine:
    """
    Rule-assisted Anti-Money Laundering (AML) typology classifier.
    """

    @classmethod
    def analyze_graph(cls, graph_data: FundFlowGraph) -> RiskTypologySummary:
        findings: List[RiskFinding] = []

        # 1. Multi-hop Layering Check (3+ hops)
        if graph_data.hop_depth >= 3:
            findings.append(RiskFinding(
                id="rf_typ01",
                typology_code="TYP-01",
                typology_name="Rapid Layering (Multi-Hop Relay)",
                severity="HIGH",
                affected_address=graph_data.suspect_wallet,
                explanation=f"Fund flow exhibits sequential multi-hop layering extending across {graph_data.hop_depth} hops.",
                evidence_tx_ids=[e.tx_id for e in graph_data.edges[:4]],
                confidence=0.88
            ))

        # 2. Mixer Exposure Check
        mixer_nodes = [n for n in graph_data.nodes if n.node_type == "MIXER"]
        if mixer_nodes:
            for m in mixer_nodes:
                findings.append(RiskFinding(
                    id=f"rf_typ04_{m.id[:6]}",
                    typology_code="TYP-04",
                    typology_name="Privacy Mixer Exposure",
                    severity="CRITICAL",
                    affected_address=m.address,
                    explanation=f"Funds interact directly with privacy tumbler / coin-mixing smart contract ({m.label or m.address}).",
                    evidence_tx_ids=[e.tx_id for e in graph_data.edges if e.target.lower() == m.id.lower() or e.source.lower() == m.id.lower()],
                    confidence=0.95
                ))

        # 3. Cross-Chain Bridge Interaction
        bridge_nodes = [n for n in graph_data.nodes if n.node_type == "BRIDGE"]
        if bridge_nodes:
            for b in bridge_nodes:
                findings.append(RiskFinding(
                    id=f"rf_typ05_{b.id[:6]}",
                    typology_code="TYP-05",
                    typology_name="Cross-Chain Liquidity Hop",
                    severity="MEDIUM",
                    affected_address=b.address,
                    explanation=f"Funds interact with cross-chain bridge gateway ({b.label or b.address}).",
                    evidence_tx_ids=[e.tx_id for e in graph_data.edges if e.target.lower() == b.id.lower() or e.source.lower() == b.id.lower()],
                    confidence=0.90
                ))

        overall_sev = "LOW"
        if any(f.severity == "CRITICAL" for f in findings):
            overall_sev = "CRITICAL"
        elif any(f.severity == "HIGH" for f in findings):
            overall_sev = "HIGH"
        elif any(f.severity == "MEDIUM" for f in findings):
            overall_sev = "MEDIUM"

        return RiskTypologySummary(
            case_id=graph_data.case_id,
            total_findings=len(findings),
            overall_risk_level=overall_sev,
            findings=findings
        )

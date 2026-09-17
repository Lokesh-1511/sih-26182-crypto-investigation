# scripts/create_demo_case.py
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.schemas.wallet import Chain
from backend.app.blockchain.adapters.fixture_adapter import FixtureBlockchainProvider
from backend.app.graph.builder import GraphBuilder
from backend.app.graph.traversal import GraphTraversalEngine
from backend.app.entities.resolver import EntityResolver
from backend.app.attribution.scorer import VASPAttributionScorer
from backend.app.attribution.counterfactual import CounterfactualEngine
from backend.app.risk.breakpoint import ObfuscationBreakpointDetector
from backend.app.risk.typologies import RiskTypologyEngine
from backend.app.reports.pdf_generator import ForensicReportGenerator
from backend.app.reports.action_packet import ActionPacketGenerator
from backend.app.evidence.snapshots import SnapshotEngine

def run_demo_case_b():
    print("==================================================")
    print("SIH 26182 - OFFLINE INVESTIGATION DEMO CASE B")
    print("==================================================")

    provider = FixtureBlockchainProvider()
    case_id = "CASE-2026-002B"
    suspect_wallet = "0x71C83e20e8F468a3E282241F8C936f4521487439"
    chain = Chain.ETH

    print(f"1. Ingesting transactions for suspect wallet: {suspect_wallet}")
    # Ingest from fixture cache
    transfers = []
    for tx in provider._cache.values():
        transfers.extend(tx.transfers)
    print(f"   Collected {len(transfers)} transfers across flow.")

    print("2. Constructing directed fund-flow graph...")
    resolver = EntityResolver()
    node_labels = {}
    for t in transfers:
        for addr in (t.from_address, t.to_address):
            resolved = resolver.resolve(addr)
            if resolved.get("entity_name"):
                node_labels[addr.lower()] = resolved

    builder = GraphBuilder()
    graph_data = builder.build_from_transfers(
        case_id=case_id,
        suspect_wallet=suspect_wallet,
        chain=chain,
        transfers=transfers,
        node_labels=node_labels
    )
    print(f"   Graph generated: {graph_data.total_nodes} nodes, {graph_data.total_edges} edges.")

    print("3. Executing Obfuscation Breakpoint Detection...")
    breakpoints = ObfuscationBreakpointDetector.detect_breakpoints(graph_data, fan_out_threshold=3)
    graph_data.breakpoints = breakpoints
    if breakpoints:
        bp = breakpoints[0]
        print(f"   [!] OBFUSCATION BREAKPOINT DETECTED at {bp.address}")
        print(f"       Signals: {bp.signals_detected}")
        print(f"       Reasoning: {bp.reasoning}")

    print("4. Evaluating VASP Attribution Scoring...")
    scorer = VASPAttributionScorer(resolver=resolver)
    attribution = scorer.evaluate_case(
        case_id=case_id,
        suspect_wallet=suspect_wallet,
        chain=chain,
        graph_data=graph_data
    )

    top_cand = attribution.top_candidate
    if top_cand:
        print(f"\n   TOP ATTRIBUTED VASP: {top_cand.entity_name}")
        print(f"   CONFIDENCE SCORE:    {top_cand.confidence_score}% ({top_cand.confidence_band})")
        print(f"   OPERATOR ROLE:       {attribution.operator_beneficiary.operator_attribution}")
        print(f"   BENEFICIARY:         {attribution.operator_beneficiary.beneficiary_identity}")
        print("\n   EXPLAINABLE EVIDENCE BREAKDOWN:")
        for f in top_cand.factors:
            sign = "+" if f.contribution_points > 0 else ""
            print(f"     * {f.factor_name:<32} {sign}{f.contribution_points} pts -> {f.description}")

        print("\n5. Running Counterfactual Sensitivity Simulation...")
        cfs = CounterfactualEngine.simulate_ablation(top_cand)
        top_cand.counterfactuals = cfs
        for cf in cfs:
            print(f"     * Ablating [{cf.factor_removed}]: Score drops from {cf.original_score}% to {cf.new_score}% (Delta: -{cf.score_delta} pts) [{cf.robustness_evaluation}]")

    print("\n6. Running AML Risk & Typology Analysis...")
    risk_summary = RiskTypologyEngine.analyze_graph(graph_data)
    print(f"   Overall Risk Level: {risk_summary.overall_risk_level}")
    for rf in risk_summary.findings:
        print(f"     * [{rf.severity}] {rf.typology_name}: {rf.explanation}")

    print("\n7. Creating Tamper-Evident Snapshot & Report...")
    snapshot = SnapshotEngine.create_snapshot(
        case_id=case_id,
        input_wallet=suspect_wallet,
        chain="ETH",
        payload_data={
            "graph": graph_data.model_dump(),
            "attribution": attribution.model_dump(),
            "risk": risk_summary.model_dump()
        }
    )
    print(f"   Snapshot SHA-256 Digest: {snapshot.integrity_hash_sha256}")

    report = ForensicReportGenerator.generate_html_report(
        case_data={"id": case_id, "investigator": "SI Ananya Sharma", "suspect_wallet": suspect_wallet, "chain": "ETH", "status": "OPEN"},
        attribution_data=attribution.model_dump(),
        risk_data=risk_summary.model_dump()
    )
    print(f"   Report exported to: {report['report_path']}")

    if top_cand:
        action_packet = ActionPacketGenerator.generate_packet(
            case_id=case_id,
            investigator="SI Ananya Sharma",
            suspect_wallet=suspect_wallet,
            chain="ETH",
            candidate=top_cand
        )
        print(f"   Lawful Action Packet generated: {action_packet.packet_id} (Target: {action_packet.attributed_vasp})")

    print("\n==================================================")
    print("SUCCESS: Full vertical slice executed offline!")
    print("==================================================")

if __name__ == "__main__":
    run_demo_case_b()

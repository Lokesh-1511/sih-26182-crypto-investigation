# scripts/validate_demo_case.py
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.schemas.wallet import Chain
from backend.app.blockchain.adapters.fixture_adapter import FixtureBlockchainProvider
from backend.app.graph.builder import GraphBuilder
from backend.app.entities.resolver import EntityResolver
from backend.app.attribution.scorer import VASPAttributionScorer
from backend.app.risk.breakpoint import ObfuscationBreakpointDetector

def validate_benchmark():
    print("Running Automated Ground-Truth Validation...")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    gt_file = os.path.join(base_dir, "data", "demo", "ground_truth", "ground_truth.json")

    with open(gt_file, "r", encoding="utf-8") as f:
        benchmarks = json.load(f)["benchmark_cases"]

    provider = FixtureBlockchainProvider()
    resolver = EntityResolver()
    scorer = VASPAttributionScorer(resolver=resolver)

    all_passed = True

    for b in benchmarks:
        cid = b["case_id"]
        suspect = b["suspect_wallet"]
        chain = Chain(b["chain"])
        expected_vasp = b["ground_truth_vasp"]
        min_score = b["expected_min_score"]

        # Collect transfers from cache for this benchmark case's chain
        transfers = []
        for tx in provider._cache.values():
            if tx.chain == chain:
                transfers.extend(tx.transfers)

        node_labels = {}
        for t in transfers:
            for addr in (t.from_address, t.to_address):
                res = resolver.resolve(addr)
                if res.get("entity_name"):
                    node_labels[addr.lower()] = res

        builder = GraphBuilder()
        graph_data = builder.build_from_transfers(cid, suspect, chain, transfers, node_labels)

        if b.get("has_breakpoint"):
            bps = ObfuscationBreakpointDetector.detect_breakpoints(graph_data)
            graph_data.breakpoints = bps
            assert len(bps) > 0, f"Failed breakpoint check for {cid}"

        attribution = scorer.evaluate_case(cid, suspect, chain, graph_data)
        top = attribution.top_candidate

        if not top:
            print(f"FAILED: {cid} yielded no VASP candidate.")
            all_passed = False
            continue

        vasp_match = (top.entity_name == expected_vasp)
        score_match = (top.confidence_score >= min_score)

        if vasp_match and score_match:
            print(f"PASSED [{cid}]: Attributed {top.entity_name} ({top.confidence_score}%) >= {min_score}%")
        else:
            print(f"FAILED [{cid}]: Got {top.entity_name} ({top.confidence_score}%), expected {expected_vasp} (>={min_score}%)")
            all_passed = False

    if all_passed:
        print("\nALL GROUND-TRUTH BENCHMARKS PASSED (Top-1 Accuracy: 100%)")
    else:
        sys.exit(1)

if __name__ == "__main__":
    validate_benchmark()

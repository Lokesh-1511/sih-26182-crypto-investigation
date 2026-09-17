# tests/unit/test_attribution.py
import pytest
from backend.app.schemas.wallet import Chain
from backend.app.blockchain.adapters.fixture_adapter import FixtureBlockchainProvider
from backend.app.graph.builder import GraphBuilder
from backend.app.entities.resolver import EntityResolver
from backend.app.attribution.scorer import VASPAttributionScorer
from backend.app.attribution.counterfactual import CounterfactualEngine

def test_attribution_and_counterfactual():
    provider = FixtureBlockchainProvider()
    case_id = "CASE-TEST-ATTR"
    suspect = "0x71C83e20e8F468a3E282241F8C936f4521487439"
    chain = Chain.ETH

    transfers = []
    for tx in provider._cache.values():
        transfers.extend(tx.transfers)

    resolver = EntityResolver()
    node_labels = {}
    for t in transfers:
        for addr in (t.from_address, t.to_address):
            res = resolver.resolve(addr)
            if res.get("entity_name"):
                node_labels[addr.lower()] = res

    builder = GraphBuilder()
    graph_data = builder.build_from_transfers(case_id, suspect, chain, transfers, node_labels)

    scorer = VASPAttributionScorer(resolver=resolver)
    attr = scorer.evaluate_case(case_id, suspect, chain, graph_data)

    assert attr.top_candidate is not None
    top = attr.top_candidate
    assert top.entity_name == "Binance"
    assert top.confidence_score >= 70.0
    assert top.confidence_band == "HIGH"
    assert attr.operator_beneficiary.beneficiary_identity == "NOT ESTABLISHED"

    # Counterfactual ablation
    cfs = CounterfactualEngine.simulate_ablation(top)
    assert len(cfs) > 0
    # Deposit match ablation delta should be significant
    dep_cf = [c for c in cfs if "Deposit" in c.factor_removed]
    if dep_cf:
        assert dep_cf[0].new_score < top.confidence_score

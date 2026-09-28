# tests/integration/test_investigation_live.py
"""
Opt-in live end-to-end test for Investigation API against real Ethereum Mainnet via Bitquery V2.
This test is OPT-IN and will only execute when RUN_LIVE_BITQUERY=1 and BITQUERY_ACCESS_TOKEN are set.
Default pytest execution will automatically skip this test.
"""
import os
import re
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

load_dotenv()

from backend.app.main import app
from backend.app.blockchain.models.enums import Chain
from backend.app.blockchain.providers.factory import ProviderFactory
from backend.app.blockchain.providers.bitquery.provider import BitqueryProvider

client = TestClient(app)

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_BITQUERY") != "1" or not os.getenv("BITQUERY_ACCESS_TOKEN"),
    reason="Live Investigation API test is opt-in. Set RUN_LIVE_BITQUERY=1 and BITQUERY_ACCESS_TOKEN to execute live queries."
)

def test_live_investigation_api_ethereum_wallet(monkeypatch):
    """
    Proves live HTTP API -> Investigation Router -> InvestigationService -> ProviderFactory ->
    BitqueryProvider -> Bitquery V2 API -> NormalizedTransfer/NormalizedTransaction ->
    TransactionCollector -> GraphBuilder -> GraphTraversalEngine -> InvestigationResponse.

    Uses small bounds: max_hops=1, max_transactions=5 to conserve Bitquery points.
    """
    # 1. Ensure live mode is configured for ProviderFactory
    monkeypatch.setenv("DATA_SOURCE_MODE", "LIVE_BITQUERY")
    
    # 2. Verify that ProviderFactory actually resolves to BitqueryProvider
    resolved_provider = ProviderFactory.get_provider()
    assert isinstance(
        resolved_provider, BitqueryProvider
    ), f"Expected BitqueryProvider under LIVE_BITQUERY mode, got {type(resolved_provider)}"

    target_wallet = "0x28C6c06298d514Db089934071355E5743bf21d60"

    # 3. Call actual FastAPI HTTP endpoint
    resp = client.post(
        "/api/v1/investigations",
        json={
            "chain": "ethereum",
            "address": target_wallet,
            "max_hops": 1,
            "max_transactions": 5
        }
    )

    # Diagnostic output on failure / logging
    print(f"\n[LIVE TEST DIAGNOSTIC] HTTP Status: {resp.status_code}")

    assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}: {resp.text}"
    data = resp.json()

    # 4. Assert Top-Level Response Structure
    assert data["status"] == "completed"
    assert data["chain"] == "ethereum"
    assert data["root_address"].lower() == target_wallet.lower()
    assert isinstance(data["investigation_id"], str) and len(data["investigation_id"]) > 0
    assert "summary" in data
    assert "graph" in data

    summary = data["summary"]
    print(f"[LIVE TEST DIAGNOSTIC] Summary: Nodes={summary.get('nodes')}, Edges={summary.get('edges')}, "
          f"Tx={summary.get('transactions')}, Transfers={summary.get('transfers')}, Hops={summary.get('hops')}")

    # 5. Assert Summary Counts
    assert summary["nodes"] >= 1
    assert summary["edges"] >= 0
    assert summary["transactions"] >= 0
    assert summary["transfers"] >= 0
    assert summary["hops"] >= 0

    # 6. Assert Graph & Nodes
    graph = data["graph"]
    assert "nodes" in graph
    assert "edges" in graph
    assert len(graph["nodes"]) >= 1

    # Root wallet must appear as SUSPECT
    root_node_matches = [
        n for n in graph["nodes"]
        if n["address"].lower() == target_wallet.lower() or n["id"].lower() == target_wallet.lower()
    ]
    assert len(root_node_matches) >= 1, f"Root wallet {target_wallet} not found in graph nodes"
    root_node = root_node_matches[0]
    assert root_node["node_type"] == "SUSPECT", f"Expected SUSPECT, got {root_node['node_type']}"

    # 7. Assert Real Blockchain Edges & Exact Amounts
    if summary["edges"] > 0:
        assert len(graph["edges"]) > 0
        tx_hash_pattern = re.compile(r"^0x[0-9a-fA-F]{64}$")

        for edge in graph["edges"]:
            assert "id" in edge
            assert "transfer_id" in edge
            assert "tx_hash" in edge
            assert "source" in edge
            assert "target" in edge
            assert "asset_id" in edge
            assert "amount" in edge
            assert "timestamp" in edge
            assert "transfer_type" in edge
            assert "evidence_ref" in edge

            # Amount must be string representation of exact Decimal
            assert isinstance(edge["amount"], str), f"Amount must be serialized as string, got {type(edge['amount'])}"

            # Tx hash must match standard EVM transaction hash format
            if edge["tx_hash"]:
                assert tx_hash_pattern.match(edge["tx_hash"]), f"Invalid tx_hash format: {edge['tx_hash']}"

    # 8. Verify No Provider Leakage
    raw_json_str = resp.text
    token = os.environ.get("BITQUERY_ACCESS_TOKEN", "")
    if token:
        assert token not in raw_json_str, "Bitquery access token leaked into HTTP response!"
    assert "graphql" not in raw_json_str.lower(), "GraphQL query/structure leaked into response!"
    assert "networkx" not in raw_json_str.lower(), "NetworkX internal structures leaked into response!"
    assert "authorization" not in raw_json_str.lower(), "Authorization header leaked into response!"

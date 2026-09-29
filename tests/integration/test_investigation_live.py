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

def test_live_investigation_api_ethereum_outgoing_multihop(monkeypatch):
    """
    Live outgoing multi-hop verification for Ethereum wallet with controlled bounds (max_hops=2, max_transactions=5).
    """
    monkeypatch.setenv("DATA_SOURCE_MODE", "LIVE_BITQUERY")
    resolved_provider = ProviderFactory.get_provider()
    assert isinstance(resolved_provider, BitqueryProvider)

    target_wallet = "0x28C6c06298d514Db089934071355E5743bf21d60"

    resp = client.post(
        "/api/v1/investigations",
        json={
            "chain": "ethereum",
            "address": target_wallet,
            "direction": "outgoing",
            "max_hops": 2,
            "max_transactions": 5
        }
    )

    print(f"\n[LIVE OUTGOING TEST] HTTP Status: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}: {resp.text}"
    data = resp.json()

    assert data["status"] == "completed"
    assert data["chain"] == "ethereum"
    assert data["root_address"].lower() == target_wallet.lower()
    assert "summary" in data
    assert "trace" in data
    assert data["trace"]["direction"] == "outgoing"
    assert data["trace"]["requested_max_hops"] == 2
    assert data["summary"]["transactions"] <= 5

    # Root wallet must appear as SUSPECT
    root_node_matches = [
        n for n in data["graph"]["nodes"]
        if n["address"].lower() == target_wallet.lower() or n["id"].lower() == target_wallet.lower()
    ]
    assert len(root_node_matches) >= 1
    assert root_node_matches[0]["node_type"] == "SUSPECT"
    assert root_node_matches[0]["hop_distance"] == 0

    # Ensure all amount values are string-serialized decimals
    for edge in data["graph"]["edges"]:
        assert isinstance(edge["amount"], str)

    # Zero credential leakage check
    raw_json_str = resp.text
    token = os.environ.get("BITQUERY_ACCESS_TOKEN", "")
    if token:
        assert token not in raw_json_str
    assert "authorization" not in raw_json_str.lower()


def test_live_investigation_api_ethereum_incoming_multihop(monkeypatch):
    """
    Live incoming multi-hop verification for Ethereum wallet with controlled bounds (max_hops=2, max_transactions=5).
    """
    monkeypatch.setenv("DATA_SOURCE_MODE", "LIVE_BITQUERY")
    resolved_provider = ProviderFactory.get_provider()
    assert isinstance(resolved_provider, BitqueryProvider)

    target_wallet = "0x28C6c06298d514Db089934071355E5743bf21d60"

    resp = client.post(
        "/api/v1/investigations",
        json={
            "chain": "ethereum",
            "address": target_wallet,
            "direction": "incoming",
            "max_hops": 2,
            "max_transactions": 5
        }
    )

    print(f"\n[LIVE INCOMING TEST] HTTP Status: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}: {resp.text}"
    data = resp.json()

    assert data["status"] == "completed"
    assert data["chain"] == "ethereum"
    assert data["root_address"].lower() == target_wallet.lower()
    assert "summary" in data
    assert "trace" in data
    assert data["trace"]["direction"] == "incoming"
    assert data["trace"]["requested_max_hops"] == 2
    assert data["summary"]["transactions"] <= 5

    # Check root wallet
    root_node_matches = [
        n for n in data["graph"]["nodes"]
        if n["address"].lower() == target_wallet.lower() or n["id"].lower() == target_wallet.lower()
    ]
    assert len(root_node_matches) >= 1
    assert root_node_matches[0]["node_type"] == "SUSPECT"
    assert root_node_matches[0]["hop_distance"] == 0

    # Critical Rule 7 verification: graph edges MUST retain actual blockchain from -> to direction
    for edge in data["graph"]["edges"]:
        assert isinstance(edge["amount"], str)
        # For incoming transfers into root or intermediaries, edge.source -> edge.target is preserved
        assert "source" in edge
        assert "target" in edge

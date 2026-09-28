# tests/integration/test_graph_pipeline.py
"""
Complete Fund-Flow Graph Pipeline Integration Test.
Proves that real blockchain-provider data correctly flows through:
Real Bitquery response -> Bitquery mapper -> NormalizedTransfer -> GraphBuilder -> NetworkX MultiDiGraph -> GraphTraversalEngine -> Dashboard-safe serialization.
Executes entirely OFFLINE by replaying captured real Bitquery fixtures (zero network consumption).
"""
import os
import json
from decimal import Decimal
from pathlib import Path
import pytest
import networkx as nx

from backend.app.blockchain.models.enums import Chain, AssetType, TransferType, TransactionStatus, TransactionType
from backend.app.blockchain.models.transfer import NormalizedTransfer
from backend.app.blockchain.models.transaction import NormalizedTransaction
from backend.app.blockchain.providers.bitquery.mapper import BitqueryEVMMapper
from backend.app.schemas.graph import FundFlowGraph, GraphNode, GraphEdge
from backend.app.graph.builder import GraphBuilder
from backend.app.graph.traversal import GraphTraversalEngine
from backend.app.graph.filters import GraphNoiseFilter
from backend.app.graph.path_analysis import PathAnalysisEngine

FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "bitquery" / "ethereum" / "transfers_real.json"
TX_FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "bitquery" / "ethereum" / "transaction_real.json"


@pytest.fixture
def real_bitquery_transfers_raw() -> list:
    """Loads captured real Bitquery Ethereum Transfers response fixture."""
    assert FIXTURE_PATH.exists(), f"Fixture missing at {FIXTURE_PATH}"
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)
    transfers = payload.get("data", {}).get("EVM", {}).get("Transfers", [])
    assert len(transfers) > 0, "Captured fixture has no transfers"
    return transfers


@pytest.fixture
def real_bitquery_transaction_raw() -> dict:
    """Loads captured real Bitquery Ethereum Transaction response fixture."""
    assert TX_FIXTURE_PATH.exists(), f"Fixture missing at {TX_FIXTURE_PATH}"
    with open(TX_FIXTURE_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)
    txs = payload.get("data", {}).get("EVM", {}).get("Transactions", [])
    assert len(txs) > 0, "Captured transaction fixture has no transactions"
    return txs[0]


# ============================================================
# 1. Real Response -> Normalized Transfer & Transaction Tests
# ============================================================

def test_real_response_to_normalized_transaction(real_bitquery_transaction_raw, real_bitquery_transfers_raw):
    """
    Passes captured real Bitquery transaction response through BitqueryEVMMapper.map_transaction.
    Verifies full field preservation, exact Decimal fee, status, hashes, and confirmation metadata.
    """
    # Map associated transfers from the transfers fixture for this transaction hash if present
    mapped_transfers = BitqueryEVMMapper.map_transfers(real_bitquery_transfers_raw)
    tx_hash = real_bitquery_transaction_raw.get("Transaction", {}).get("Hash")
    matching_transfers = [t for t in mapped_transfers if t.tx_hash.lower() == tx_hash.lower()]

    norm_tx = BitqueryEVMMapper.map_transaction(real_bitquery_transaction_raw, attached_transfers=matching_transfers)

    assert isinstance(norm_tx, NormalizedTransaction)
    assert norm_tx.chain == Chain.ETHEREUM
    assert norm_tx.tx_hash == tx_hash
    assert norm_tx.tx_hash.startswith("0x")
    assert len(norm_tx.tx_hash) == 66

    # Block metadata
    assert norm_tx.block_number == 26075791
    assert norm_tx.block_hash.startswith("0x")
    assert norm_tx.timestamp is not None

    # Status & Type
    assert norm_tx.status == TransactionStatus.CONFIRMED
    assert norm_tx.transaction_type in (
        TransactionType.TOKEN_TRANSFER,
        TransactionType.CONTRACT_CALL,
        TransactionType.NATIVE_TRANSFER,
        TransactionType.MIXED
    )

    # Fee in exact Decimal
    assert isinstance(norm_tx.fee, Decimal)
    assert norm_tx.fee >= Decimal("0")
    assert norm_tx.fee_asset == "ETH"

    # Raw reference & payload hash
    assert norm_tx.raw_reference == f"bitquery://evm/eth/tx/{tx_hash}"
    assert norm_tx.raw_payload_hash is not None
    assert len(norm_tx.raw_payload_hash) == 64  # SHA-256 hex string

    # Confirmation
    assert norm_tx.confirmation is not None
    assert norm_tx.confirmation.confirmed is True

    # Associated transfers
    if matching_transfers:
        assert len(norm_tx.transfers) == len(matching_transfers)
        assert norm_tx.transfers[0].transfer_id is not None


def test_real_response_to_normalized_transfers(real_bitquery_transfers_raw):
    """
    Passes captured real Bitquery response through the real BitqueryEVMMapper.
    Verifies full field preservation, exact Decimal conversion, and identity derivation.
    """
    mapped_transfers = BitqueryEVMMapper.map_transfers(real_bitquery_transfers_raw)

    assert len(mapped_transfers) == len(real_bitquery_transfers_raw)
    assert len(mapped_transfers) >= 5

    for transfer in mapped_transfers:
        # Canonical type
        assert isinstance(transfer, NormalizedTransfer)
        assert transfer.chain == Chain.ETHEREUM

        # Identity & Hash
        assert transfer.transfer_id is not None
        assert transfer.transfer_id.startswith("ethereum:")
        assert transfer.tx_hash.startswith("0x")
        assert len(transfer.tx_hash) == 66  # Standard 32-byte hex hash

        # Addresses
        assert transfer.from_address.startswith("0x")
        assert transfer.to_address.startswith("0x")
        assert len(transfer.from_address) == 42
        assert len(transfer.to_address) == 42

        # Asset & Precision
        assert transfer.asset_id is not None
        assert transfer.asset_symbol is not None
        assert isinstance(transfer.raw_amount, str)
        assert isinstance(transfer.normalized_amount, Decimal)
        assert transfer.normalized_amount > Decimal("0")

        # Timestamp & Evidence
        assert transfer.timestamp is not None
        assert transfer.evidence_ref is not None
        assert transfer.evidence_ref.startswith("bitquery://evm/eth/tx/")

        # Transfer type classification
        assert transfer.transfer_type in (TransferType.TOKEN, TransferType.NATIVE, TransferType.INTERNAL)


# ============================================================
# 2. Normalized Transfers -> Graph Construction Test
# ============================================================

def test_normalized_transfers_to_graph_pipeline(real_bitquery_transfers_raw):
    """
    Constructs a NetworkX MultiDiGraph from mapped NormalizedTransfers.
    Verifies that every transfer becomes a distinct traceable edge with transfer_id key.
    """
    mapped_transfers = BitqueryEVMMapper.map_transfers(real_bitquery_transfers_raw)
    root_wallet = "0x28c6c06298d514db089934071355e5743bf21d60"

    builder = GraphBuilder()
    graph_data: FundFlowGraph = builder.build_from_transfers(
        case_id="CASE-REAL-PIPELINE",
        suspect_wallet=root_wallet,
        chain=Chain.ETH,
        transfers=mapped_transfers
    )

    # Underlying NetworkX engine
    assert isinstance(builder.graph, nx.MultiDiGraph)
    assert builder.graph.number_of_nodes() == graph_data.total_nodes
    assert builder.graph.number_of_edges() == graph_data.total_edges

    # Edge preservation: no transfer is lost
    assert graph_data.total_edges == len(mapped_transfers)

    # Suspect node is root
    suspect_node = next(n for n in graph_data.nodes if n.id == root_wallet.lower())
    assert suspect_node.node_type == "SUSPECT"
    assert suspect_node.address == root_wallet

    # Every transfer exists as an edge with key == transfer_id
    for t in mapped_transfers:
        src = t.from_address.lower()
        dst = t.to_address.lower()
        assert builder.graph.has_node(src)
        assert builder.graph.has_node(dst)

        # Check edge exists in MultiDiGraph under its transfer_id
        edge_data = builder.graph.get_edge_data(src, dst, key=t.transfer_id)
        assert edge_data is not None, f"Edge missing for key {t.transfer_id}"
        assert edge_data["transfer_id"] == t.transfer_id
        assert edge_data["tx_hash"] == t.tx_hash
        assert edge_data["amount"] == t.normalized_amount
        assert isinstance(edge_data["amount"], Decimal)
        assert edge_data["evidence_ref"] == t.evidence_ref


# ============================================================
# 3. Graph Structural Validation & Multi-Edge Preservation
# ============================================================

def test_graph_structural_integrity_and_parallel_edges(real_bitquery_transfers_raw):
    """
    Validates structural counts and explicitly tests that parallel edges
    between identical address pairs survive without being overwritten.
    """
    mapped_transfers = BitqueryEVMMapper.map_transfers(real_bitquery_transfers_raw)
    root_wallet = "0x28c6c06298d514db089934071355e5743bf21d60"

    # Inject an intentional parallel transfer between an existing (src, dst) pair
    first_t = mapped_transfers[0]
    parallel_transfer = NormalizedTransfer(
        transfer_id=f"{first_t.transfer_id}_parallel_test",
        tx_hash=first_t.tx_hash,
        chain=Chain.ETHEREUM,
        from_address=first_t.from_address,
        to_address=first_t.to_address,
        asset_type=AssetType.NATIVE,
        asset_id="ETH",
        asset_symbol="ETH",
        raw_amount="500000000000000000",
        normalized_amount=Decimal("0.5"),
        transfer_type=TransferType.NATIVE,
        transfer_index=99,
        timestamp=first_t.timestamp,
        evidence_ref=f"{first_t.evidence_ref}_parallel"
    )

    combined_transfers = mapped_transfers + [parallel_transfer]

    builder = GraphBuilder()
    graph_data = builder.build_from_transfers("CASE-STRUCT", root_wallet, Chain.ETH, combined_transfers)

    # Edge count must strictly equal the transfer count
    assert graph_data.total_edges == len(combined_transfers)
    assert builder.graph.number_of_edges() == len(combined_transfers)

    # Check that parallel edges between the same (src, dst) both exist in the MultiDiGraph
    src = first_t.from_address.lower()
    dst = first_t.to_address.lower()
    edges_between = builder.graph.get_edge_data(src, dst)

    assert len(edges_between) >= 2
    assert first_t.transfer_id in edges_between
    assert parallel_transfer.transfer_id in edges_between
    assert edges_between[parallel_transfer.transfer_id]["amount"] == Decimal("0.5")


# ============================================================
# 4. Traversal Test (Outgoing, Incoming, Any Direction)
# ============================================================

def test_graph_traversal_on_real_data(real_bitquery_transfers_raw):
    """
    Tests GraphTraversalEngine across outgoing, incoming, and any directions
    starting from the root suspect wallet of the real fixture.
    """
    mapped_transfers = BitqueryEVMMapper.map_transfers(real_bitquery_transfers_raw)
    root_wallet = "0x28c6c06298d514db089934071355e5743bf21d60"

    builder = GraphBuilder()
    builder.build_from_transfers("CASE-TRAVERSAL", root_wallet, Chain.ETH, mapped_transfers)

    # A. Outgoing traversal
    out_res = GraphTraversalEngine.traverse_bfs(
        builder.graph,
        root_address=root_wallet,
        direction="outgoing",
        max_hops=1
    )
    assert root_wallet.lower() in out_res["visited_nodes"]
    assert out_res["max_depth_reached"] in (0, 1)
    for edge in out_res["edges"]:
        assert edge["_traversal_source"] == root_wallet.lower()

    # B. Incoming traversal
    in_res = GraphTraversalEngine.traverse_bfs(
        builder.graph,
        root_address=root_wallet,
        direction="incoming",
        max_hops=1
    )
    assert root_wallet.lower() in in_res["visited_nodes"]
    for edge in in_res["edges"]:
        assert edge["_traversal_target"] == root_wallet.lower()

    # C. Any direction traversal
    any_res = GraphTraversalEngine.traverse_bfs(
        builder.graph,
        root_address=root_wallet,
        direction="any",
        max_hops=1
    )
    assert len(any_res["visited_nodes"]) >= max(len(out_res["visited_nodes"]), len(in_res["visited_nodes"]))
    assert any_res["total_edges_traversed"] >= max(len(out_res["edges"]), len(in_res["edges"]))


# ============================================================
# 5. Multi-Hop and Cycle Safety Tests
# ============================================================

def test_graph_multi_hop_expansion():
    """
    Verifies that increasing max_hops (1 -> 2 -> 3) discovers additional downstream nodes.
    Uses a controlled multi-hop chain: Root -> Intermediary1 -> Intermediary2 -> TerminalVASP.
    """
    root = "0xroot"
    hop1 = "0xhop1"
    hop2 = "0xhop2"
    terminal = "0xterminal"

    transfers = [
        NormalizedTransfer(transfer_id="t1", tx_hash="0xtx1", chain=Chain.ETH, from_address=root, to_address=hop1, normalized_amount=Decimal("10"), asset_symbol="ETH"),
        NormalizedTransfer(transfer_id="t2", tx_hash="0xtx2", chain=Chain.ETH, from_address=hop1, to_address=hop2, normalized_amount=Decimal("5"), asset_symbol="ETH"),
        NormalizedTransfer(transfer_id="t3", tx_hash="0xtx3", chain=Chain.ETH, from_address=hop2, to_address=terminal, normalized_amount=Decimal("2"), asset_symbol="ETH"),
    ]

    builder = GraphBuilder()
    builder.build_from_transfers("CASE-MULTIHOP", root, Chain.ETH, transfers)

    # 1 Hop
    h1 = GraphTraversalEngine.traverse_bfs(builder.graph, root, max_hops=1)
    assert set(h1["visited_nodes"]) == {root.lower(), hop1.lower()}
    assert h1["max_depth_reached"] == 1

    # 2 Hops
    h2 = GraphTraversalEngine.traverse_bfs(builder.graph, root, max_hops=2)
    assert set(h2["visited_nodes"]) == {root.lower(), hop1.lower(), hop2.lower()}
    assert h2["max_depth_reached"] == 2

    # 3 Hops (discovers terminal VASP)
    h3 = GraphTraversalEngine.traverse_bfs(builder.graph, root, max_hops=3)
    assert set(h3["visited_nodes"]) == {root.lower(), hop1.lower(), hop2.lower(), terminal.lower()}
    assert h3["max_depth_reached"] == 3


def test_graph_cycle_safety_and_limits():
    """
    Verifies that cyclical flow (A -> B -> C -> A) terminates safely,
    respects max_hops, and enforces max_nodes/max_edges limits.
    """
    a = "0xnode_a"
    b = "0xnode_b"
    c = "0xnode_c"

    cyclic_transfers = [
        NormalizedTransfer(transfer_id="e_ab", tx_hash="tx1", chain=Chain.ETH, from_address=a, to_address=b, normalized_amount=Decimal("1.0"), asset_symbol="ETH"),
        NormalizedTransfer(transfer_id="e_bc", tx_hash="tx2", chain=Chain.ETH, from_address=b, to_address=c, normalized_amount=Decimal("1.0"), asset_symbol="ETH"),
        NormalizedTransfer(transfer_id="e_ca", tx_hash="tx3", chain=Chain.ETH, from_address=c, to_address=a, normalized_amount=Decimal("1.0"), asset_symbol="ETH"),
    ]

    builder = GraphBuilder()
    builder.build_from_transfers("CASE-CYCLE-SAFE", a, Chain.ETH, cyclic_transfers)

    # Traversal must terminate despite cycle
    res = GraphTraversalEngine.traverse_bfs(builder.graph, a, max_hops=5)
    assert set(res["visited_nodes"]) == {a.lower(), b.lower(), c.lower()}
    assert len(res["visited_nodes"]) == 3

    # Node limit constraint
    res_lim = GraphTraversalEngine.traverse_bfs(builder.graph, a, max_nodes=2)
    assert len(res_lim["visited_nodes"]) <= 2


# ============================================================
# 6. Decimal Money Precision & Transfer Traceability
# ============================================================

def test_decimal_money_correctness_and_traceability(real_bitquery_transfers_raw):
    """
    Verifies that financial transfer amounts are exact Decimals from raw response to graph edges,
    and that every graph edge can be traced back to its originating normalized transfer.
    """
    mapped_transfers = BitqueryEVMMapper.map_transfers(real_bitquery_transfers_raw)
    root_wallet = "0x28c6c06298d514db089934071355e5743bf21d60"

    builder = GraphBuilder()
    graph_data = builder.build_from_transfers("CASE-PRECISION", root_wallet, Chain.ETH, mapped_transfers)

    transfer_lookup = {t.transfer_id: t for t in mapped_transfers}

    for edge in graph_data.edges:
        # 1. Decimal type check
        assert isinstance(edge.amount, Decimal), f"Edge amount {edge.amount} is not Decimal"
        assert not isinstance(edge.amount, float)

        # 2. Traceability link back to source transfer
        orig = transfer_lookup.get(edge.transfer_id)
        assert orig is not None, f"Edge {edge.transfer_id} cannot be traced to mapped transfer"
        assert edge.tx_hash == orig.tx_hash
        assert edge.amount == orig.normalized_amount
        assert edge.asset_symbol == orig.asset_symbol
        assert edge.evidence_ref == orig.evidence_ref
        assert edge.source == orig.from_address.lower()
        assert edge.target == orig.to_address.lower()


# ============================================================
# 7. Dashboard-Safe Serialization & Determinism
# ============================================================

def test_dashboard_safe_serialization_and_determinism(real_bitquery_transfers_raw):
    """
    Tests that FundFlowGraph serializes into a clean, JSON-serializable dashboard payload
    without leaking NetworkX or Python-specific internal objects.
    Verifies that repeated serializations with permuted inputs produce identical output.
    """
    mapped_transfers = BitqueryEVMMapper.map_transfers(real_bitquery_transfers_raw)
    root_wallet = "0x28c6c06298d514db089934071355e5743bf21d60"

    builder1 = GraphBuilder()
    graph1 = builder1.build_from_transfers("CASE-DASHBOARD", root_wallet, Chain.ETH, mapped_transfers)

    # Permuted input order
    builder2 = GraphBuilder()
    graph2 = builder2.build_from_transfers("CASE-DASHBOARD", root_wallet, Chain.ETH, list(reversed(mapped_transfers)))

    # Serializations
    json_str1 = graph1.model_dump_json()
    json_str2 = graph2.model_dump_json()

    # Determinism assertion
    assert json_str1 == json_str2

    # Parse and validate JSON structure
    payload = json.loads(json_str1)
    assert "nodes" in payload
    assert "edges" in payload
    assert payload["case_id"] == "CASE-DASHBOARD"
    assert payload["suspect_wallet"] == root_wallet
    assert payload["chain"] == "ethereum"

    # Validate node schema
    for node in payload["nodes"]:
        assert "id" in node
        assert "address" in node
        assert "chain" in node
        assert "node_type" in node

    # Validate edge schema
    for edge in payload["edges"]:
        assert "id" in edge
        assert "transfer_id" in edge
        assert "tx_hash" in edge
        assert "source" in edge
        assert "target" in edge
        assert "asset_symbol" in edge
        assert "amount" in edge
        assert "transfer_type" in edge
        assert "evidence_ref" in edge


# ============================================================
# 8. Provider-Agnostic Verification
# ============================================================

def test_graph_layer_remains_strictly_provider_agnostic():
    """
    Inspects backend/app/graph modules to assert that zero Bitquery, GraphQL,
    or RPC client imports exist in the graph layer.
    """
    graph_dir = Path(__file__).parent.parent.parent / "backend" / "app" / "graph"
    assert graph_dir.exists()

    forbidden_keywords = ["bitquery", "BitqueryClient", "graphql", "BitqueryProvider", "BitqueryEVMMapper"]

    for py_file in graph_dir.glob("*.py"):
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()
        for kw in forbidden_keywords:
            assert kw.lower() not in content.lower(), f"Forbidden keyword '{kw}' found in {py_file.name}"

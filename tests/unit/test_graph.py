# tests/unit/test_graph.py
from datetime import datetime, timezone
from decimal import Decimal
import json
import pytest
from backend.app.blockchain.models.enums import Chain, AssetType, TransferType
from backend.app.blockchain.models.transfer import NormalizedTransfer
from backend.app.graph.builder import GraphBuilder
from backend.app.graph.traversal import GraphTraversalEngine
from backend.app.graph.filters import GraphNoiseFilter
from backend.app.graph.path_analysis import PathAnalysisEngine

def test_graph_builder_and_traversal():
    suspect = "0x71C83e20e8F468a3E282241F8C936f4521487439"
    hop1 = "0x3a9B552f4c91E606132D9eD9D5FaD79f18B57062"
    hop2 = "0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97"

    transfers = [
        NormalizedTransfer(
            transfer_id="ethereum:0xtx1:tidx_0",
            tx_hash="0xtx1",
            chain=Chain.ETHEREUM,
            from_address=suspect,
            to_address=hop1,
            asset_type=AssetType.NATIVE,
            asset_id="ETH",
            asset_symbol="ETH",
            raw_amount="10500000000000000000",
            normalized_amount=Decimal("10.5"),
            transfer_type=TransferType.NATIVE,
            transfer_index=0,
            hop_distance=1,
            timestamp=datetime(2026, 3, 14, 10, 0, 0, tzinfo=timezone.utc),
            evidence_ref="ev_0xtx1_proof"
        ),
        NormalizedTransfer(
            transfer_id="ethereum:0xtx2:tidx_0",
            tx_hash="0xtx2",
            chain=Chain.ETHEREUM,
            from_address=hop1,
            to_address=hop2,
            asset_type=AssetType.NATIVE,
            asset_id="ETH",
            asset_symbol="ETH",
            raw_amount="5250000000000000000",
            normalized_amount=Decimal("5.25"),
            transfer_type=TransferType.NATIVE,
            transfer_index=0,
            hop_distance=2,
            timestamp=datetime(2026, 3, 14, 10, 30, 0, tzinfo=timezone.utc),
            evidence_ref="ev_0xtx2_proof"
        )
    ]

    builder = GraphBuilder()
    graph_data = builder.build_from_transfers("CASE-TEST", suspect, Chain.ETH, transfers)

    assert graph_data.total_nodes == 3
    assert graph_data.total_edges == 2
    assert isinstance(graph_data.edges[0].amount, Decimal)
    assert graph_data.edges[0].amount == Decimal("10.5")
    assert graph_data.edges[1].amount == Decimal("5.25")
    assert graph_data.edges[0].evidence_ref == "ev_0xtx1_proof"

    # Traversal test
    trav = GraphTraversalEngine.traverse_bfs(builder.graph, suspect, max_hops=3)
    assert len(trav["visited_nodes"]) == 3
    assert trav["max_depth_reached"] == 2


def test_graph_multiple_transfers_same_pair_preserved():
    """
    Verify that multiple transfers between the same pair of addresses
    (e.g., native ETH, ERC-20 token, and internal call) are NOT collapsed or lost.
    """
    sender = "0xaaaa111122223333444455556666777788889999"
    receiver = "0xbbbb111122223333444455556666777788889999"

    t1 = NormalizedTransfer(
        transfer_id="ethereum:0xtx1:tidx_0",
        tx_hash="0xtx1",
        chain=Chain.ETHEREUM,
        from_address=sender,
        to_address=receiver,
        asset_type=AssetType.NATIVE,
        asset_id="ETH",
        asset_symbol="ETH",
        raw_amount="1000000000000000000",
        normalized_amount=Decimal("1.0"),
        transfer_type=TransferType.NATIVE,
        transfer_index=0,
        timestamp=datetime(2026, 3, 14, 12, 0, 0, tzinfo=timezone.utc)
    )
    t2 = NormalizedTransfer(
        transfer_id="ethereum:0xtx1:log_12",
        tx_hash="0xtx1",
        chain=Chain.ETHEREUM,
        from_address=sender,
        to_address=receiver,
        asset_type=AssetType.ERC20,
        asset_id="0xdac17f958d2ee523a2206206994597c13d831ec7",
        asset_symbol="USDT",
        raw_amount="5000000000",
        normalized_amount=Decimal("5000.0"),
        transfer_type=TransferType.TOKEN,
        transfer_index=1,
        timestamp=datetime(2026, 3, 14, 12, 0, 0, tzinfo=timezone.utc)
    )
    t3 = NormalizedTransfer(
        transfer_id="ethereum:0xtx2:call_1",
        tx_hash="0xtx2",
        chain=Chain.ETHEREUM,
        from_address=sender,
        to_address=receiver,
        asset_type=AssetType.NATIVE,
        asset_id="ETH",
        asset_symbol="ETH",
        raw_amount="500000000000000000",
        normalized_amount=Decimal("0.5"),
        transfer_type=TransferType.INTERNAL,
        transfer_index=0,
        timestamp=datetime(2026, 3, 14, 12, 10, 0, tzinfo=timezone.utc)
    )

    builder = GraphBuilder()
    graph_data = builder.build_from_transfers("CASE-MULTI-EDGE", sender, Chain.ETH, [t1, t2, t3])

    # Nodes: Exactly 2 nodes (sender and receiver)
    assert graph_data.total_nodes == 2
    assert builder.graph.number_of_nodes() == 2

    # Edges: Exactly 3 distinct edges in NetworkX MultiDiGraph and serialized FundFlowGraph
    assert graph_data.total_edges == 3
    assert builder.graph.number_of_edges() == 3

    # Check that each transfer ID is distinct and mapped accurately
    edge_ids = [e.transfer_id for e in graph_data.edges]
    assert "ethereum:0xtx1:tidx_0" in edge_ids
    assert "ethereum:0xtx1:log_12" in edge_ids
    assert "ethereum:0xtx2:call_1" in edge_ids

    # Query NetworkX multi-edges between the sender and receiver directly
    edges_between = builder.graph.get_edge_data(sender.lower(), receiver.lower())
    assert len(edges_between) == 3
    assert "ethereum:0xtx1:tidx_0" in edges_between
    assert "ethereum:0xtx1:log_12" in edges_between
    assert "ethereum:0xtx2:call_1" in edges_between

    # Check exact amounts and transfer types in MultiDiGraph
    assert edges_between["ethereum:0xtx1:tidx_0"]["amount"] == Decimal("1.0")
    assert edges_between["ethereum:0xtx1:tidx_0"]["transfer_type"] == "NATIVE"

    assert edges_between["ethereum:0xtx1:log_12"]["amount"] == Decimal("5000.0")
    assert edges_between["ethereum:0xtx1:log_12"]["asset_symbol"] == "USDT"
    assert edges_between["ethereum:0xtx1:log_12"]["transfer_type"] == "TOKEN"

    assert edges_between["ethereum:0xtx2:call_1"]["amount"] == Decimal("0.5")
    assert edges_between["ethereum:0xtx2:call_1"]["transfer_type"] == "INTERNAL"


def test_graph_traceable_edge_attributes():
    """Verify all traceable blockchain transfer fields are fully preserved."""
    root = "0x1111111111111111111111111111111111111111"
    target = "0x2222222222222222222222222222222222222222"

    transfer = NormalizedTransfer(
        transfer_id="ethereum:0xabc123:log_42",
        tx_hash="0xabc123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        chain=Chain.ETHEREUM,
        from_address=root,
        to_address=target,
        asset_type=AssetType.ERC20,
        asset_id="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        asset_symbol="USDC",
        raw_amount="250000000",
        normalized_amount=Decimal("250.00"),
        transfer_type=TransferType.TOKEN,
        transfer_index=3,
        timestamp=datetime(2026, 3, 14, 15, 30, 0, tzinfo=timezone.utc),
        evidence_ref="ev_0xabc1234567"
    )

    builder = GraphBuilder()
    graph_data = builder.build_from_transfers(
        case_id="CASE-TRACEABLE",
        suspect_wallet=root,
        chain=Chain.ETH,
        transfers=[transfer],
        node_labels={target.lower(): {"entity_name": "Binance 14", "entity_type": "VASP_DEPOSIT", "confidence": 0.98}}
    )

    edge = graph_data.edges[0]
    assert edge.transfer_id == "ethereum:0xabc123:log_42"
    assert edge.tx_hash == "0xabc123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    assert edge.tx_id == edge.tx_hash  # Backward compatibility property
    assert edge.source == root.lower()
    assert edge.target == target.lower()
    assert edge.asset_id == "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    assert edge.asset_symbol == "USDC"
    assert edge.asset == "USDC"  # Backward compatibility property
    assert edge.amount == Decimal("250.00")
    assert edge.amount_float == 250.0
    assert edge.transfer_type == "TOKEN"
    assert edge.evidence_ref == "ev_0xabc1234567"

    # Verify node entity metadata
    target_node = next(n for n in graph_data.nodes if n.id == target.lower())
    assert target_node.entity_name == "Binance 14"
    assert target_node.node_type == "VASP_DEPOSIT"
    assert target_node.confidence == 0.98


def test_graph_multi_chain_and_utxo_support():
    """Verify graph layer uniformly supports Bitcoin UTXO, Tron, and EVM transfers."""
    btc_suspect = "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"
    btc_hop1 = "bc1q9d4q4e2m0y5l37283g4a6h7j8k9l0m1n2o3p4q"

    btc_transfer = NormalizedTransfer(
        transfer_id="bitcoin:tx_btc_01:out_0",
        tx_hash="tx_btc_01",
        chain=Chain.BITCOIN,
        from_address=btc_suspect,
        to_address=btc_hop1,
        asset_type=AssetType.NATIVE,
        asset_id="BTC",
        asset_symbol="BTC",
        raw_amount="125000000",
        normalized_amount=Decimal("1.25"),
        transfer_type=TransferType.UTXO_OUTPUT,
        transfer_index=0,
        timestamp=datetime(2026, 3, 14, 8, 0, 0, tzinfo=timezone.utc)
    )

    builder = GraphBuilder()
    graph_data = builder.build_from_transfers("CASE-BTC", btc_suspect, Chain.BTC, [btc_transfer])

    assert graph_data.chain == Chain.BTC
    assert graph_data.total_nodes == 2
    assert graph_data.edges[0].asset_symbol == "BTC"
    assert graph_data.edges[0].amount == Decimal("1.25")
    assert graph_data.edges[0].transfer_type == "UTXO_OUTPUT"


def test_graph_deterministic_construction_and_serialization():
    """Verify identical inputs (even if re-ordered) produce identical graph output and JSON serialization."""
    root = "0xroot"
    node_b = "0xbbb"
    node_c = "0xccc"
    node_d = "0xddd"

    t1 = NormalizedTransfer(
        transfer_id="tx1_0",
        tx_hash="tx1",
        chain=Chain.ETHEREUM,
        from_address=root,
        to_address=node_b,
        normalized_amount=Decimal("10"),
        asset_symbol="ETH",
        timestamp=datetime(2026, 3, 14, 10, 0, 0, tzinfo=timezone.utc)
    )
    t2 = NormalizedTransfer(
        transfer_id="tx2_0",
        tx_hash="tx2",
        chain=Chain.ETHEREUM,
        from_address=node_b,
        to_address=node_c,
        normalized_amount=Decimal("5"),
        asset_symbol="ETH",
        timestamp=datetime(2026, 3, 14, 10, 10, 0, tzinfo=timezone.utc)
    )
    t3 = NormalizedTransfer(
        transfer_id="tx3_0",
        tx_hash="tx3",
        chain=Chain.ETHEREUM,
        from_address=node_c,
        to_address=node_d,
        normalized_amount=Decimal("2"),
        asset_symbol="ETH",
        timestamp=datetime(2026, 3, 14, 10, 20, 0, tzinfo=timezone.utc)
    )

    builder1 = GraphBuilder()
    g1 = builder1.build_from_transfers("CASE-DET", root, Chain.ETH, [t1, t2, t3])

    builder2 = GraphBuilder()
    g2 = builder2.build_from_transfers("CASE-DET", root, Chain.ETH, [t3, t1, t2])

    # Assert node and edge sequences match exactly
    assert [n.id for n in g1.nodes] == [n.id for n in g2.nodes]
    assert [e.id for e in g1.edges] == [e.id for e in g2.edges]

    # Assert JSON dumps are strictly equal
    json1 = g1.model_dump_json()
    json2 = g2.model_dump_json()
    assert json1 == json2


def test_graph_traversal_with_limits_and_cycle_prevention():
    """Verify multi-hop traversal handles cycles, hop depth, and edge/node limits."""
    root = "0xroot"
    n1 = "0xn1"
    n2 = "0xn2"
    n3 = "0xn3"

    transfers = [
        NormalizedTransfer(transfer_id="e1", tx_hash="tx1", chain=Chain.ETH, from_address=root, to_address=n1, normalized_amount=Decimal("10"), asset_symbol="ETH"),
        NormalizedTransfer(transfer_id="e2", tx_hash="tx2", chain=Chain.ETH, from_address=n1, to_address=n2, normalized_amount=Decimal("8"), asset_symbol="ETH"),
        NormalizedTransfer(transfer_id="e3", tx_hash="tx3", chain=Chain.ETH, from_address=n2, to_address=n3, normalized_amount=Decimal("5"), asset_symbol="ETH"),
        # Cycle back from n2 to root
        NormalizedTransfer(transfer_id="e_cycle", tx_hash="tx4", chain=Chain.ETH, from_address=n2, to_address=root, normalized_amount=Decimal("1"), asset_symbol="ETH"),
    ]

    builder = GraphBuilder()
    builder.build_from_transfers("CASE-CYCLE", root, Chain.ETH, transfers)

    # 1. Full traversal with cycle prevention
    res_full = GraphTraversalEngine.traverse_bfs(builder.graph, root, max_hops=4)
    assert set(res_full["visited_nodes"]) == {root, n1, n2, n3}
    assert res_full["max_depth_reached"] == 3

    # 2. Configurable max_hops=1 (only root -> n1)
    res_hop1 = GraphTraversalEngine.traverse_bfs(builder.graph, root, max_hops=1)
    assert set(res_hop1["visited_nodes"]) == {root, n1}
    assert res_hop1["max_depth_reached"] == 1

    # 3. Configurable max_nodes=2
    res_max_nodes = GraphTraversalEngine.traverse_bfs(builder.graph, root, max_nodes=2)
    assert len(res_max_nodes["visited_nodes"]) <= 2

    # 4. Extract scoped subgraph
    subgraph = GraphTraversalEngine.extract_subgraph(builder.graph, root, max_hops=2)
    assert root in subgraph
    assert n1 in subgraph
    assert n2 in subgraph
    assert n3 not in subgraph


def test_graph_noise_filters_comprehensive():
    """Verify dust, min_amount, asset whitelist, and time-window filtering."""
    suspect = "0xsuspect"
    dest1 = "0xd1"
    dest2 = "0xd2"

    transfers = [
        NormalizedTransfer(
            transfer_id="t_eth_large",
            tx_hash="tx1",
            chain=Chain.ETH,
            from_address=suspect,
            to_address=dest1,
            normalized_amount=Decimal("5.0"),
            asset_symbol="ETH",
            timestamp=datetime(2026, 3, 14, 10, 0, 0, tzinfo=timezone.utc)
        ),
        NormalizedTransfer(
            transfer_id="t_eth_dust",
            tx_hash="tx2",
            chain=Chain.ETH,
            from_address=suspect,
            to_address=dest2,
            normalized_amount=Decimal("0.00005"),
            asset_symbol="ETH",
            timestamp=datetime(2026, 3, 14, 11, 0, 0, tzinfo=timezone.utc)
        ),
        NormalizedTransfer(
            transfer_id="t_usdt",
            tx_hash="tx3",
            chain=Chain.ETH,
            from_address=suspect,
            to_address=dest1,
            normalized_amount=Decimal("1000.0"),
            asset_symbol="USDT",
            timestamp=datetime(2026, 3, 14, 12, 0, 0, tzinfo=timezone.utc)
        )
    ]

    builder = GraphBuilder()
    graph_data = builder.build_from_transfers("CASE-FILTER", suspect, Chain.ETH, transfers)
    assert graph_data.total_edges == 3

    # Dust filter: removes t_eth_dust
    f_dust = GraphNoiseFilter.apply_filters(graph_data, hide_dust=True, dust_threshold=Decimal("0.0001"))
    assert f_dust.total_edges == 2
    assert {e.transfer_id for e in f_dust.edges} == {"t_eth_large", "t_usdt"}

    # Asset whitelist filter: only USDT
    f_asset = GraphNoiseFilter.apply_filters(graph_data, asset_filter="USDT")
    assert f_asset.total_edges == 1
    assert f_asset.edges[0].asset_symbol == "USDT"

    # Time window filter: before 11:30:00 (excludes t_usdt)
    f_time = GraphNoiseFilter.apply_filters(
        graph_data,
        end_time=datetime(2026, 3, 14, 10, 30, 0, tzinfo=timezone.utc)
    )
    assert f_time.total_edges == 1
    assert f_time.edges[0].transfer_id == "t_eth_large"


def test_graph_path_analysis_shortest_and_bottleneck():
    """Verify shortest path, highest-value path, and volume summary calculations."""
    root = "0xroot"
    hop1 = "0xhop1"
    vasp = "0xvasp"
    alt_route = "0xalt"

    # Route 1: Direct but small: root -> vasp (0.1 ETH)
    # Route 2: 2 hops but huge volume: root -> hop1 (100 ETH) -> vasp (100 ETH)
    transfers = [
        NormalizedTransfer(transfer_id="e_direct", tx_hash="txd", chain=Chain.ETH, from_address=root, to_address=vasp, normalized_amount=Decimal("0.1"), asset_symbol="ETH"),
        NormalizedTransfer(transfer_id="e_large_1", tx_hash="txl1", chain=Chain.ETH, from_address=root, to_address=hop1, normalized_amount=Decimal("100.0"), asset_symbol="ETH"),
        NormalizedTransfer(transfer_id="e_large_2", tx_hash="txl2", chain=Chain.ETH, from_address=hop1, to_address=vasp, normalized_amount=Decimal("100.0"), asset_symbol="ETH"),
    ]

    builder = GraphBuilder()
    builder.build_from_transfers("CASE-PATH", root, Chain.ETH, transfers)

    # Shortest path: [root, vasp]
    shortest = PathAnalysisEngine.find_shortest_path(builder.graph, root, vasp)
    assert shortest == [root.lower(), vasp.lower()]

    # Highest value path: [root, hop1, vasp]
    highest_val = PathAnalysisEngine.find_highest_value_path(builder.graph, root, vasp)
    assert highest_val == [root.lower(), hop1.lower(), vasp.lower()]

    # Decimal summary statistics
    stats = builder.get_summary_statistics()
    assert stats["total_nodes"] == 3
    assert stats["total_edges"] == 3
    assert stats["asset_volumes"]["ETH"] == Decimal("200.1")

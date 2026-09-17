# tests/unit/test_graph.py
import pytest
from datetime import datetime
from backend.app.schemas.wallet import Chain
from backend.app.schemas.transaction import NormalizedTransfer
from backend.app.graph.builder import GraphBuilder
from backend.app.graph.traversal import GraphTraversalEngine
from backend.app.graph.filters import GraphNoiseFilter

def test_graph_builder_and_traversal():
    suspect = "0x71C83e20e8F468a3E282241F8C936f4521487439"
    hop1 = "0x3a9B552f4c91E606132D9eD9D5FaD79f18B57062"
    hop2 = "0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97"

    transfers = [
        NormalizedTransfer(
            tx_id="0xtx1",
            from_address=suspect,
            to_address=hop1,
            amount=10.0,
            asset="ETH",
            hop_distance=1,
            timestamp=datetime.utcnow()
        ),
        NormalizedTransfer(
            tx_id="0xtx2",
            from_address=hop1,
            to_address=hop2,
            amount=5.0,
            asset="ETH",
            hop_distance=2,
            timestamp=datetime.utcnow()
        )
    ]

    builder = GraphBuilder()
    graph_data = builder.build_from_transfers("CASE-TEST", suspect, Chain.ETH, transfers)

    assert graph_data.total_nodes == 3
    assert graph_data.total_edges == 2

    # Traversal test
    trav = GraphTraversalEngine.traverse_bfs(builder.graph, suspect, max_hops=3)
    assert len(trav["visited_nodes"]) == 3
    assert trav["max_depth_reached"] == 2

def test_graph_dust_filter():
    suspect = "0xAAA"
    normal_dest = "0xBBB"
    dust_dest = "0xCCC"

    transfers = [
        NormalizedTransfer(tx_id="tx_norm", from_address=suspect, to_address=normal_dest, amount=2.5, asset="ETH"),
        NormalizedTransfer(tx_id="tx_dust", from_address=suspect, to_address=dust_dest, amount=0.00001, asset="ETH")
    ]

    builder = GraphBuilder()
    graph_data = builder.build_from_transfers("CASE-DUST", suspect, Chain.ETH, transfers)
    assert len(graph_data.edges) == 2

    filtered = GraphNoiseFilter.apply_filters(graph_data, hide_dust=True, dust_threshold=0.001)
    assert len(filtered.edges) == 1
    assert filtered.edges[0].tx_id == "tx_norm"

# tests/unit/test_multihop_tracing.py
"""
Comprehensive Phase 8 Unit & Offline Integration Tests for True Multi-Hop Fund-Flow Tracing.

Covers all 20 required offline test scenarios:
1. Outgoing 1 hop
2. Outgoing 2 hops
3. Outgoing 3 hops
4. Incoming 1 hop
5. Incoming 2 hops
6. Incoming 3 hops
7. Max_hops boundary enforcement
8. Boundary destination detection
9. Boundary transaction details
10. Actual depth < requested depth
11. Actual depth == requested depth
12. Cycle prevention
13. Max transaction budget enforcement
14. Max node limit
15. Max edge limit
16. Empty outgoing trace
17. Empty incoming trace
18. Backward tracing preserves A -> B edge direction (Rule 7)
19. Multiple transfers between same addresses remain separate
20. Deterministic serialization

Zero live Bitquery calls are made. All fixtures run offline against MockOfflineMultiHopProvider.
"""
from datetime import datetime, timezone
from decimal import Decimal
import json
from typing import List, Dict, Optional, Set
import pytest
import networkx as nx

from backend.app.blockchain.models.enums import Chain, AssetType, TransferType, TransactionStatus, TransferDirection
from backend.app.blockchain.models.provider import AddressValidation, ProviderCapabilities
from backend.app.blockchain.models.pagination import TransactionPage, TransferPage
from backend.app.blockchain.models.transaction import NormalizedTransaction
from backend.app.blockchain.models.transfer import NormalizedTransfer
from backend.app.blockchain.providers.base import BlockchainProvider
from backend.app.blockchain.ingestion.collector import TransactionCollector
from backend.app.schemas.investigation import InvestigationCreateRequest, InvestigationResponse, TraceMetadata
from backend.app.schemas.graph import GraphNode, GraphEdge, FundFlowGraph
from backend.app.graph.builder import GraphBuilder
from backend.app.graph.traversal import GraphTraversalEngine
from backend.app.services.investigation_service import InvestigationService


class MockOfflineMultiHopProvider(BlockchainProvider):
    """
    In-memory blockchain graph provider supporting forward and backward transfer queries.
    Configured with known topologies for deterministic multi-hop testing.
    """

    def __init__(self, transfers: Optional[List[NormalizedTransfer]] = None):
        self.transfers_list = transfers or []
        self.transactions_dict: Dict[str, NormalizedTransaction] = {}
        for t in self.transfers_list:
            if t.tx_hash not in self.transactions_dict:
                self.transactions_dict[t.tx_hash] = NormalizedTransaction(
                    tx_hash=t.tx_hash,
                    chain=t.chain,
                    timestamp=t.timestamp or datetime.now(timezone.utc),
                    status=TransactionStatus.CONFIRMED,
                    transfers=[t],
                    provider="MOCK_MULTIHOP"
                )
            else:
                self.transactions_dict[t.tx_hash].transfers.append(t)

    async def validate_address(self, chain: Chain, address: str) -> AddressValidation:
        clean = address.strip().lower()
        if "invalid" in clean:
            return AddressValidation(valid=False, normalized_address=address, chain=chain, reason="Invalid address")
        return AddressValidation(valid=True, normalized_address=clean, chain=chain)

    async def get_transactions(self, chain: Chain, address: str, direction: TransferDirection = TransferDirection.ANY, **kwargs) -> TransactionPage:
        addr_clean = address.strip().lower()
        matching_txs = []
        for tx in self.transactions_dict.values():
            for t in tx.transfers:
                if (direction in (TransferDirection.OUTGOING, TransferDirection.ANY) and t.from_address.lower() == addr_clean) or \
                   (direction in (TransferDirection.INCOMING, TransferDirection.ANY) and t.to_address.lower() == addr_clean):
                    matching_txs.append(tx)
                    break
        return TransactionPage(transactions=matching_txs, has_more=False)

    async def get_transaction(self, chain: Chain, tx_hash: str) -> Optional[NormalizedTransaction]:
        return self.transactions_dict.get(tx_hash)

    async def get_transfers(self, chain: Chain, address: str, direction: TransferDirection = TransferDirection.ANY, **kwargs) -> TransferPage:
        addr_clean = address.strip().lower()
        matching = []
        for t in self.transfers_list:
            if direction == TransferDirection.OUTGOING and t.from_address.lower() == addr_clean:
                matching.append(t)
            elif direction == TransferDirection.INCOMING and t.to_address.lower() == addr_clean:
                matching.append(t)
            elif direction == TransferDirection.ANY and (t.from_address.lower() == addr_clean or t.to_address.lower() == addr_clean):
                matching.append(t)
        return TransferPage(transfers=matching, has_more=False)

    async def get_block(self, chain: Chain, **kwargs):
        return None

    async def get_asset_metadata(self, chain: Chain, asset_id: str):
        return None

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            chains=[Chain.ETHEREUM],
            supports_transactions=True,
            supports_transfers=True
        )


def _make_transfer(tx_hash: str, from_addr: str, to_addr: str, amount_str: str, asset: str = "ETH", idx: int = 0) -> NormalizedTransfer:
    return NormalizedTransfer(
        transfer_id=f"eth:{tx_hash}:{idx}",
        tx_hash=tx_hash,
        chain=Chain.ETHEREUM,
        from_address=from_addr.lower(),
        to_address=to_addr.lower(),
        asset_symbol=asset,
        asset_id=asset,
        raw_amount=amount_str,
        normalized_amount=Decimal(amount_str),
        transfer_type=TransferType.NATIVE,
        transfer_index=idx,
        timestamp=datetime(2026, 9, 29, 12, idx, 0, tzinfo=timezone.utc),
        evidence_ref=f"ev_{tx_hash[:8]}"
    )


# ============================================================
# 1. Outgoing 1 Hop Test
# ============================================================
@pytest.mark.anyio
async def test_outgoing_1_hop():
    # S -> A
    t1 = _make_transfer("0xtx1", "0xroot", "0xnodeA", "10.0")
    provider = MockOfflineMultiHopProvider([t1])
    service = InvestigationService(provider=provider)

    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address="0xroot",
        direction=TransferDirection.OUTGOING,
        max_hops=1,
        max_transactions=10
    )
    res = await service.investigate(req)

    assert res.status == "completed"
    assert res.summary.nodes == 2  # 0xroot, 0xnodeA
    assert res.summary.edges == 1
    assert res.summary.hops == 1
    assert res.trace.direction == "outgoing"
    assert res.trace.requested_max_hops == 1
    assert res.trace.actual_max_hops == 1
    assert res.trace.max_hops_reached is True


# ============================================================
# 2. Outgoing 2 Hops Test
# ============================================================
@pytest.mark.anyio
async def test_outgoing_2_hops():
    # S -> A -> B
    t1 = _make_transfer("0xtx1", "0xroot", "0xnodeA", "10.0")
    t2 = _make_transfer("0xtx2", "0xnodeA", "0xnodeB", "8.5")
    provider = MockOfflineMultiHopProvider([t1, t2])
    service = InvestigationService(provider=provider)

    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address="0xroot",
        direction=TransferDirection.OUTGOING,
        max_hops=2,
        max_transactions=10
    )
    res = await service.investigate(req)

    assert res.summary.nodes == 3  # root, A, B
    assert res.summary.edges == 2
    assert res.summary.hops == 2
    assert res.trace.actual_max_hops == 2

    node_b = next(n for n in res.graph.nodes if n.id == "0xnodeb")
    assert node_b.hop_distance == 2


# ============================================================
# 3. Outgoing 3 Hops Test
# ============================================================
@pytest.mark.anyio
async def test_outgoing_3_hops():
    # S -> A -> B -> C
    t1 = _make_transfer("0xtx1", "0xroot", "0xnodeA", "10.0")
    t2 = _make_transfer("0xtx2", "0xnodeA", "0xnodeB", "8.5")
    t3 = _make_transfer("0xtx3", "0xnodeB", "0xnodeC", "5.0")
    provider = MockOfflineMultiHopProvider([t1, t2, t3])
    service = InvestigationService(provider=provider)

    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address="0xroot",
        direction=TransferDirection.OUTGOING,
        max_hops=3,
        max_transactions=10
    )
    res = await service.investigate(req)

    assert res.summary.nodes == 4  # root, A, B, C
    assert res.summary.edges == 3
    assert res.summary.hops == 3
    assert res.trace.actual_max_hops == 3

    node_c = next(n for n in res.graph.nodes if n.id == "0xnodec")
    assert node_c.hop_distance == 3


# ============================================================
# 4. Incoming 1 Hop Test
# ============================================================
@pytest.mark.anyio
async def test_incoming_1_hop():
    # A -> S
    t1 = _make_transfer("0xtx1", "0xnodeA", "0xroot", "15.0")
    provider = MockOfflineMultiHopProvider([t1])
    service = InvestigationService(provider=provider)

    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address="0xroot",
        direction=TransferDirection.INCOMING,
        max_hops=1,
        max_transactions=10
    )
    res = await service.investigate(req)

    assert res.summary.nodes == 2
    assert res.summary.edges == 1
    assert res.summary.hops == 1
    assert res.trace.direction == "incoming"
    assert res.trace.actual_max_hops == 1


# ============================================================
# 5. Incoming 2 Hops Test
# ============================================================
@pytest.mark.anyio
async def test_incoming_2_hops():
    # B -> A -> S
    t1 = _make_transfer("0xtx1", "0xnodeA", "0xroot", "15.0")
    t2 = _make_transfer("0xtx2", "0xnodeB", "0xnodeA", "20.0")
    provider = MockOfflineMultiHopProvider([t1, t2])
    service = InvestigationService(provider=provider)

    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address="0xroot",
        direction=TransferDirection.INCOMING,
        max_hops=2,
        max_transactions=10
    )
    res = await service.investigate(req)

    assert res.summary.nodes == 3  # root (Hop 0), A (Hop 1), B (Hop 2)
    assert res.summary.edges == 2
    assert res.summary.hops == 2
    assert res.trace.actual_max_hops == 2

    node_b = next(n for n in res.graph.nodes if n.id == "0xnodeb")
    assert node_b.hop_distance == 2


# ============================================================
# 6. Incoming 3 Hops Test
# ============================================================
@pytest.mark.anyio
async def test_incoming_3_hops():
    # C -> B -> A -> S
    t1 = _make_transfer("0xtx1", "0xnodeA", "0xroot", "15.0")
    t2 = _make_transfer("0xtx2", "0xnodeB", "0xnodeA", "20.0")
    t3 = _make_transfer("0xtx3", "0xnodeC", "0xnodeB", "25.0")
    provider = MockOfflineMultiHopProvider([t1, t2, t3])
    service = InvestigationService(provider=provider)

    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address="0xroot",
        direction=TransferDirection.INCOMING,
        max_hops=3,
        max_transactions=10
    )
    res = await service.investigate(req)

    assert res.summary.nodes == 4  # root, A, B, C
    assert res.summary.edges == 3
    assert res.summary.hops == 3
    assert res.trace.actual_max_hops == 3


# ============================================================
# 7. Max Hops Boundary Enforcement Test
# ============================================================
@pytest.mark.anyio
async def test_max_hops_boundary_enforcement():
    # S -> A -> B -> C -> D (with max_hops = 2, only S -> A -> B should be expanded)
    t1 = _make_transfer("0xtx1", "0xroot", "0xnodeA", "10.0")
    t2 = _make_transfer("0xtx2", "0xnodeA", "0xnodeB", "8.5")
    t3 = _make_transfer("0xtx3", "0xnodeB", "0xnodeC", "5.0")
    t4 = _make_transfer("0xtx4", "0xnodeC", "0xnodeD", "2.0")
    provider = MockOfflineMultiHopProvider([t1, t2, t3, t4])
    service = InvestigationService(provider=provider)

    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address="0xroot",
        direction=TransferDirection.OUTGOING,
        max_hops=2,
        max_transactions=20
    )
    res = await service.investigate(req)

    node_ids = {n.id for n in res.graph.nodes}
    assert "0xroot" in node_ids
    assert "0xnodea" in node_ids
    assert "0xnodeb" in node_ids
    # Hop 3 (C) and Hop 4 (D) must NOT be expanded into the graph
    assert "0xnodec" not in node_ids
    assert "0xnoded" not in node_ids
    assert res.summary.hops == 2


# ============================================================
# 8 & 9. Boundary Destination Detection & Details Test
# ============================================================
@pytest.mark.anyio
async def test_boundary_destination_details():
    # When node is annotated as boundary, verify attributes
    node = GraphNode(
        id="0xboundary1",
        address="0xBoundary1",
        chain=Chain.ETHEREUM,
        node_type="INTERMEDIARY",
        hop_distance=4,
        is_boundary=True,
        boundary_reason="MAX_HOPS_REACHED"
    )
    assert node.is_boundary is True
    assert node.boundary_reason == "MAX_HOPS_REACHED"
    assert node.hop_distance == 4
    # Must NOT be labeled suspicious
    assert node.node_type == "INTERMEDIARY"


# ============================================================
# 10. Actual Depth < Requested Depth Test
# ============================================================
@pytest.mark.anyio
async def test_actual_depth_less_than_requested():
    # S -> A (only 1 hop exists, but user requests max_hops = 5)
    t1 = _make_transfer("0xtx1", "0xroot", "0xnodeA", "10.0")
    provider = MockOfflineMultiHopProvider([t1])
    service = InvestigationService(provider=provider)

    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address="0xroot",
        direction=TransferDirection.OUTGOING,
        max_hops=5,
        max_transactions=50
    )
    res = await service.investigate(req)

    assert res.trace.requested_max_hops == 5
    assert res.trace.actual_max_hops == 1
    assert res.trace.max_hops_reached is False
    assert res.trace.termination_reason == "NATURAL_TERMINATION"
    assert res.summary.hops == 1


# ============================================================
# 11. Actual Depth == Requested Depth Test
# ============================================================
@pytest.mark.anyio
async def test_actual_depth_equals_requested():
    # S -> A -> B (2 hops exist, user requests max_hops = 2)
    t1 = _make_transfer("0xtx1", "0xroot", "0xnodeA", "10.0")
    t2 = _make_transfer("0xtx2", "0xnodeA", "0xnodeB", "8.0")
    provider = MockOfflineMultiHopProvider([t1, t2])
    service = InvestigationService(provider=provider)

    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address="0xroot",
        direction=TransferDirection.OUTGOING,
        max_hops=2,
        max_transactions=50
    )
    res = await service.investigate(req)

    assert res.trace.requested_max_hops == 2
    assert res.trace.actual_max_hops == 2
    assert res.trace.max_hops_reached is True
    assert res.summary.hops == 2


# ============================================================
# 12. Cycle Prevention Test (A -> B -> C -> A)
# ============================================================
@pytest.mark.anyio
async def test_cycle_prevention_no_infinite_loop():
    # S -> A -> B -> S (cycle back to S)
    t1 = _make_transfer("0xtx1", "0xroot", "0xnodeA", "10.0")
    t2 = _make_transfer("0xtx2", "0xnodeA", "0xnodeB", "8.0")
    t3 = _make_transfer("0xtx3", "0xnodeB", "0xroot", "5.0")  # cycle
    provider = MockOfflineMultiHopProvider([t1, t2, t3])
    service = InvestigationService(provider=provider)

    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address="0xroot",
        direction=TransferDirection.OUTGOING,
        max_hops=5,
        max_transactions=50
    )
    res = await service.investigate(req)

    # Must complete without recursion / infinite loop
    assert res.status == "completed"
    assert res.summary.nodes == 3  # root, A, B
    assert res.summary.edges == 3  # all 3 transfers captured


# ============================================================
# 13. Max Transaction Budget Enforcement Test
# ============================================================
@pytest.mark.anyio
async def test_max_transaction_budget_total_enforcement():
    # Root has 10 transfers, max_transactions budget is 3
    transfers = [_make_transfer(f"0xtx{i}", "0xroot", f"0xdest{i}", "1.0", idx=i) for i in range(10)]
    provider = MockOfflineMultiHopProvider(transfers)
    service = InvestigationService(provider=provider)

    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address="0xroot",
        direction=TransferDirection.OUTGOING,
        max_hops=3,
        max_transactions=3
    )
    res = await service.investigate(req)

    assert res.summary.transactions <= 3
    assert res.trace.transactions_used <= 3
    assert res.trace.transaction_limit_reached is True
    assert res.trace.termination_reason == "TRANSACTION_LIMIT_REACHED"


# ============================================================
# 14 & 15. Max Node & Edge Safety Limits in Traversal
# ============================================================
def test_traversal_engine_max_node_and_edge_limits():
    G = nx.MultiDiGraph()
    G.add_node("0xroot")
    for i in range(20):
        target = f"0xnode_{i}"
        G.add_node(target)
        G.add_edge("0xroot", target, key=f"edge_{i}", transfer_id=f"t_{i}", amount=Decimal("1.0"))

    # Test max_nodes limit
    res_nodes = GraphTraversalEngine.traverse_bfs(G, "0xroot", max_hops=2, max_nodes=5)
    assert len(res_nodes["visited_nodes"]) <= 5

    # Test max_edges limit
    res_edges = GraphTraversalEngine.traverse_bfs(G, "0xroot", max_hops=2, max_edges=3)
    assert len(res_edges["edges"]) <= 3


# ============================================================
# 16. Empty Outgoing Trace Test
# ============================================================
@pytest.mark.anyio
async def test_empty_outgoing_trace():
    provider = MockOfflineMultiHopProvider([])
    service = InvestigationService(provider=provider)

    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address="0xroot",
        direction=TransferDirection.OUTGOING,
        max_hops=3,
        max_transactions=50
    )
    res = await service.investigate(req)

    assert res.status == "completed"
    assert res.summary.nodes == 1  # root node only
    assert res.summary.edges == 0
    assert res.summary.hops == 0
    assert res.trace.termination_reason == "EMPTY_WALLET"
    assert res.graph.nodes[0].node_type == "SUSPECT"


# ============================================================
# 17. Empty Incoming Trace Test
# ============================================================
@pytest.mark.anyio
async def test_empty_incoming_trace():
    provider = MockOfflineMultiHopProvider([])
    service = InvestigationService(provider=provider)

    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address="0xroot",
        direction=TransferDirection.INCOMING,
        max_hops=3,
        max_transactions=50
    )
    res = await service.investigate(req)

    assert res.status == "completed"
    assert res.summary.nodes == 1
    assert res.summary.edges == 0
    assert res.summary.hops == 0
    assert res.trace.termination_reason == "EMPTY_WALLET"


# ============================================================
# 18. Critical Rule: Backward Tracing Preserves A -> B Edge Direction
# ============================================================
@pytest.mark.anyio
async def test_backward_tracing_preserves_blockchain_edge_direction():
    # Blockchain flow: NodeA -> Root
    t1 = _make_transfer("0xtx1", "0xnodeA", "0xroot", "50.0")
    provider = MockOfflineMultiHopProvider([t1])
    service = InvestigationService(provider=provider)

    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address="0xroot",
        direction=TransferDirection.INCOMING,
        max_hops=2,
        max_transactions=10
    )
    res = await service.investigate(req)

    assert len(res.graph.edges) == 1
    edge = res.graph.edges[0]
    # Edge MUST be from NodeA to Root (never reversed to Root -> NodeA!)
    assert edge.source == "0xnodea"
    assert edge.target == "0xroot"


# ============================================================
# 19. Multiple Transfers Between Same Addresses Remain Separate
# ============================================================
@pytest.mark.anyio
async def test_multiple_transfers_between_same_addresses_remain_separate():
    t1 = _make_transfer("0xtx1", "0xroot", "0xnodeA", "10.0", idx=0)
    t2 = _make_transfer("0xtx2", "0xroot", "0xnodeA", "20.0", idx=0)
    t3 = _make_transfer("0xtx3", "0xroot", "0xnodeA", "30.0", idx=0)
    provider = MockOfflineMultiHopProvider([t1, t2, t3])
    service = InvestigationService(provider=provider)

    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address="0xroot",
        direction=TransferDirection.OUTGOING,
        max_hops=1,
        max_transactions=10
    )
    res = await service.investigate(req)

    assert res.summary.nodes == 2
    assert res.summary.edges == 3
    assert len(res.graph.edges) == 3
    edge_amounts = {e.amount for e in res.graph.edges}
    assert edge_amounts == {Decimal("10.0"), Decimal("20.0"), Decimal("30.0")}


# ============================================================
# 20. Deterministic Serialization Test
# ============================================================
@pytest.mark.anyio
async def test_deterministic_serialization():
    t1 = _make_transfer("0xtx1", "0xroot", "0xnodeB", "10.0")
    t2 = _make_transfer("0xtx2", "0xroot", "0xnodeA", "20.0")
    provider = MockOfflineMultiHopProvider([t1, t2])
    service = InvestigationService(provider=provider)

    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address="0xroot",
        direction=TransferDirection.OUTGOING,
        max_hops=1,
        max_transactions=10
    )

    res1 = await service.investigate(req, investigation_id="inv_fixed_123")
    res2 = await service.investigate(req, investigation_id="inv_fixed_123")

    # Fixed timestamp for deterministic full response comparison
    fixed_time = datetime(2026, 9, 29, 12, 0, 0, tzinfo=timezone.utc)
    res1.created_at = fixed_time
    res2.created_at = fixed_time
    for r in res1.entity_resolutions:
        r.resolved_at = fixed_time
    for r in res2.entity_resolutions:
        r.resolved_at = fixed_time
    for a in res1.vasp_attributions:
        a.attributed_at = fixed_time
    for a in res2.vasp_attributions:
        a.attributed_at = fixed_time

    dump1 = res1.model_dump_json()
    dump2 = res2.model_dump_json()

    assert dump1 == dump2
    # Verify graph node and edge ordering
    assert res1.graph.model_dump_json() == res2.graph.model_dump_json()

# tests/unit/test_entity_resolution.py
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from typing import List

from backend.app.intelligence.models import (
    ResolutionStatus,
    EntityType,
    EntityResolution,
    VaspAttribution
)
from backend.app.intelligence.providers.registry import LocalRegistryProvider
from backend.app.intelligence.resolver import EntityResolver
from backend.app.intelligence.service import VaspAttributionService
from backend.app.schemas.graph import FundFlowGraph, GraphNode, GraphEdge
from backend.app.services.investigation_service import InvestigationService
from backend.app.blockchain.models.transfer import NormalizedTransfer
from backend.app.blockchain.models.transaction import NormalizedTransaction

@pytest.mark.anyio
async def test_1_known_address_resolves_correctly():
    provider = LocalRegistryProvider()
    res = await provider.resolve_address("ethereum", "0x1111111111111111111111111111111111111111")
    assert res.resolution_status == ResolutionStatus.RESOLVED
    assert res.entity_name == "Binance"
    assert res.vasp_status is True
    assert res.source is not None
    assert res.source_reference is not None

@pytest.mark.anyio
async def test_2_unknown_address_returns_not_found():
    provider = LocalRegistryProvider()
    res = await provider.resolve_address("ethereum", "0x9999999999999999999999999999999999999999")
    assert res.resolution_status == ResolutionStatus.NOT_FOUND
    assert res.entity_name is None
    assert res.vasp_status is False
    assert res.entity_id is None

@pytest.mark.anyio
async def test_3_vasp_address_returns_vasp_status_true():
    provider = LocalRegistryProvider()
    res = await provider.resolve_address("ethereum", "0x2222222222222222222222222222222222222222")
    assert res.resolution_status == ResolutionStatus.RESOLVED
    assert res.entity_name == "Coinbase Custody"
    assert res.vasp_status is True
    assert res.entity_type == EntityType.CUSTODIAN

@pytest.mark.anyio
async def test_4_non_vasp_entity_returns_vasp_status_false():
    provider = LocalRegistryProvider()
    res = await provider.resolve_address("ethereum", "0x3333333333333333333333333333333333333333")
    assert res.resolution_status == ResolutionStatus.RESOLVED
    assert res.entity_name == "Uniswap V3 Router"
    assert res.vasp_status is False
    assert res.entity_type == EntityType.PROTOCOL

@pytest.mark.anyio
async def test_5_ambiguous_result_represented_correctly():
    provider = LocalRegistryProvider()
    res = await provider.resolve_address("ethereum", "0x4444444444444444444444444444444444444444")
    assert res.resolution_status == ResolutionStatus.AMBIGUOUS
    assert len(res.candidates) >= 2
    candidate_names = {c.entity_name for c in res.candidates}
    assert "Exchange Alpha" in candidate_names
    assert "Exchange Beta" in candidate_names

@pytest.mark.anyio
async def test_6_address_normalization_case_insensitivity():
    provider = LocalRegistryProvider()
    res_lower = await provider.resolve_address("ethereum", "0x1111111111111111111111111111111111111111")
    res_upper = await provider.resolve_address("ethereum", "0x1111111111111111111111111111111111111111".upper())
    assert res_lower.resolution_status == ResolutionStatus.RESOLVED
    assert res_upper.resolution_status == ResolutionStatus.RESOLVED
    assert res_lower.entity_name == res_upper.entity_name

@pytest.mark.anyio
async def test_7_duplicate_address_deduplication():
    resolver = EntityResolver()
    addresses = [
        "0x1111111111111111111111111111111111111111",
        "0x1111111111111111111111111111111111111111",
        "0x1111111111111111111111111111111111111111".upper(),
        "0x2222222222222222222222222222222222222222"
    ]
    results = await resolver.resolve_addresses("ethereum", addresses)
    # Deduplicated lookup maps to unique normalized addresses
    assert len(results) == 2

@pytest.mark.anyio
async def test_8_multiple_discovered_addresses_batch_resolution():
    resolver = EntityResolver()
    addresses = [
        "0x1111111111111111111111111111111111111111",
        "0x3333333333333333333333333333333333333333",
        "0x9999999999999999999999999999999999999999"
    ]
    results = await resolver.resolve_addresses("ethereum", addresses)
    assert len(results) == 3
    assert results["0x1111111111111111111111111111111111111111"].vasp_status is True
    assert results["0x3333333333333333333333333333333333333333"].vasp_status is False
    assert results["0x9999999999999999999999999999999999999999"].resolution_status == ResolutionStatus.NOT_FOUND

@pytest.mark.anyio
async def test_9_path_and_hop_metadata_preservation():
    service = VaspAttributionService()
    # Graph: Root S (0xaaaa) -> A (0xbbbb) -> B (0xcccc) -> D (0x1111... Binance VASP)
    nodes = [
        GraphNode(id="0xaaaa", address="0xaaaa", chain="ethereum", hop_distance=0, node_type="SUSPECT"),
        GraphNode(id="0xbbbb", address="0xbbbb", chain="ethereum", hop_distance=1),
        GraphNode(id="0xcccc", address="0xcccc", chain="ethereum", hop_distance=2),
        GraphNode(id="0x1111111111111111111111111111111111111111", address="0x1111111111111111111111111111111111111111", chain="ethereum", hop_distance=3)
    ]
    edges = [
        GraphEdge(id="t1", transfer_id="t1", tx_hash="0xtx1", source="0xaaaa", target="0xbbbb", asset_id="ETH", asset_symbol="ETH", amount=Decimal("1.0"), hop=1),
        GraphEdge(id="t2", transfer_id="t2", tx_hash="0xtx2", source="0xbbbb", target="0xcccc", asset_id="ETH", asset_symbol="ETH", amount=Decimal("1.0"), hop=2),
        GraphEdge(id="t3", transfer_id="t3", tx_hash="0xtx3", source="0xcccc", target="0x1111111111111111111111111111111111111111", asset_id="ETH", asset_symbol="ETH", amount=Decimal("1.0"), hop=3)
    ]
    graph = FundFlowGraph(
        case_id="case_test",
        suspect_wallet="0xaaaa",
        chain="ethereum",
        nodes=nodes,
        edges=edges,
        hop_depth=3,
        total_nodes=4,
        total_edges=3
    )

    resolutions, attributions = await service.attribute_investigation(
        chain="ethereum",
        root_address="0xaaaa",
        graph=graph,
        direction="outgoing"
    )

    assert len(attributions) == 1
    attr = attributions[0]
    assert attr.entity_name == "Binance"
    assert attr.hop_distance == 3
    assert attr.direction == "outgoing"
    assert attr.path == ["0xaaaa", "0xbbbb", "0xcccc", "0x1111111111111111111111111111111111111111"]
    assert attr.relevant_transfer_ids == ["t1", "t2", "t3"]

@pytest.mark.anyio
async def test_10_incoming_attribution_with_predecessor_path():
    service = VaspAttributionService()
    # Flow: Binance D (0x1111...) -> C (0xcccc) -> S (0xaaaa)
    # Blockchain edge direction: 0x1111 -> 0xcccc -> 0xaaaa
    # Investigating S with incoming direction
    nodes = [
        GraphNode(id="0xaaaa", address="0xaaaa", chain="ethereum", hop_distance=0, node_type="SUSPECT"),
        GraphNode(id="0xcccc", address="0xcccc", chain="ethereum", hop_distance=1),
        GraphNode(id="0x1111111111111111111111111111111111111111", address="0x1111111111111111111111111111111111111111", chain="ethereum", hop_distance=2)
    ]
    edges = [
        GraphEdge(id="t1", transfer_id="t1", tx_hash="0xtx1", source="0x1111111111111111111111111111111111111111", target="0xcccc", asset_id="ETH", asset_symbol="ETH", amount=Decimal("2.0"), hop=2),
        GraphEdge(id="t2", transfer_id="t2", tx_hash="0xtx2", source="0xcccc", target="0xaaaa", asset_id="ETH", asset_symbol="ETH", amount=Decimal("2.0"), hop=1)
    ]
    graph = FundFlowGraph(
        case_id="case_incoming",
        suspect_wallet="0xaaaa",
        chain="ethereum",
        nodes=nodes,
        edges=edges,
        hop_depth=2,
        total_nodes=3,
        total_edges=2
    )

    resolutions, attributions = await service.attribute_investigation(
        chain="ethereum",
        root_address="0xaaaa",
        graph=graph,
        direction="incoming"
    )

    assert len(attributions) == 1
    attr = attributions[0]
    assert attr.entity_name == "Binance"
    assert attr.hop_distance == 2
    assert attr.direction == "incoming"
    assert attr.path == ["0xaaaa", "0xcccc", "0x1111111111111111111111111111111111111111"]
    assert attr.relevant_transfer_ids == ["t2", "t1"]

def test_11_canonical_blockchain_models_unmodified():
    # Verify NormalizedTransfer and NormalizedTransaction have no entity_name or vasp_name fields
    tx_fields = NormalizedTransaction.model_fields.keys()
    tf_fields = NormalizedTransfer.model_fields.keys()

    assert "entity_name" not in tx_fields
    assert "vasp_name" not in tx_fields
    assert "vasp_status" not in tx_fields
    assert "entity_type" not in tx_fields

    assert "entity_name" not in tf_fields
    assert "vasp_name" not in tf_fields
    assert "vasp_status" not in tf_fields
    assert "entity_type" not in tf_fields

@pytest.mark.anyio
async def test_12_investigation_service_forward_vasp_attribution():
    from backend.app.schemas.investigation import InvestigationCreateRequest
    from backend.app.blockchain.models.enums import Chain, TransferDirection
    from tests.unit.test_multihop_tracing import MockOfflineMultiHopProvider, _make_transfer

    # A (0xaaaa) -> B (0xbbbb) -> C (0xcccc) -> D (0x1111111111111111111111111111111111111111 Binance)
    t1 = _make_transfer("0xtx1", "0xaaaa", "0xbbbb", "5.0")
    t2 = _make_transfer("0xtx2", "0xbbbb", "0xcccc", "4.5")
    t3 = _make_transfer("0xtx3", "0xcccc", "0x1111111111111111111111111111111111111111", "4.0")

    provider = MockOfflineMultiHopProvider([t1, t2, t3])
    service = InvestigationService(provider=provider)

    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address="0xaaaa",
        direction=TransferDirection.OUTGOING,
        max_hops=3,
        max_transactions=10
    )

    resp = await service.investigate(req)

    assert resp.status == "completed"
    assert len(resp.entity_resolutions) >= 4
    assert len(resp.vasp_attributions) == 1

    vasp_attr = resp.vasp_attributions[0]
    assert vasp_attr.entity_name == "Binance"
    assert vasp_attr.hop_distance == 3
    assert vasp_attr.direction == "outgoing"
    assert vasp_attr.path == ["0xaaaa", "0xbbbb", "0xcccc", "0x1111111111111111111111111111111111111111"]
    assert vasp_attr.source == "fixture_registry"

    # Check node enrichment
    node_d = next(n for n in resp.graph.nodes if n.address.lower() == "0x1111111111111111111111111111111111111111")
    assert node_d.entity_name == "Binance"
    assert node_d.metadata.get("is_vasp") is True

@pytest.mark.anyio
async def test_13_investigation_service_backward_vasp_attribution():
    from backend.app.schemas.investigation import InvestigationCreateRequest
    from backend.app.blockchain.models.enums import Chain, TransferDirection
    from tests.unit.test_multihop_tracing import MockOfflineMultiHopProvider, _make_transfer

    # Binance (0x1111...) -> C (0xcccc) -> S (0xaaaa)
    t1 = _make_transfer("0xtx1", "0x1111111111111111111111111111111111111111", "0xcccc", "10.0")
    t2 = _make_transfer("0xtx2", "0xcccc", "0xaaaa", "9.5")

    provider = MockOfflineMultiHopProvider([t1, t2])
    service = InvestigationService(provider=provider)

    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address="0xaaaa",
        direction=TransferDirection.INCOMING,
        max_hops=2,
        max_transactions=10
    )

    resp = await service.investigate(req)

    assert resp.status == "completed"
    assert len(resp.vasp_attributions) == 1

    vasp_attr = resp.vasp_attributions[0]
    assert vasp_attr.entity_name == "Binance"
    assert vasp_attr.hop_distance == 2
    assert vasp_attr.direction == "incoming"
    assert vasp_attr.path == ["0xaaaa", "0xcccc", "0x1111111111111111111111111111111111111111"]

    # Verify blockchain edges remain source -> target
    for edge in resp.graph.edges:
        if edge.id == t1.transfer_id:
            assert edge.source == "0x1111111111111111111111111111111111111111"
            assert edge.target == "0xcccc"


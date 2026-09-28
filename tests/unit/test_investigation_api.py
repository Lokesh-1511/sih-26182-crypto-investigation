# tests/unit/test_investigation_api.py
"""
Unit tests for Investigation API and InvestigationService.
Exercises request validation, service orchestration, error mapping, empty wallet handling,
and provider-agnostic response formatting using mocks and offline fixtures.
Zero live Bitquery calls are made.
"""
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import httpx

from backend.app.main import app
from backend.app.blockchain.models.enums import Chain, AssetType, TransferType, TransactionStatus
from backend.app.blockchain.models.provider import AddressValidation, ProviderCapabilities
from backend.app.blockchain.models.pagination import TransactionPage, TransferPage
from backend.app.blockchain.models.transaction import NormalizedTransaction
from backend.app.blockchain.models.transfer import NormalizedTransfer
from backend.app.blockchain.providers.base import BlockchainProvider
from backend.app.blockchain.providers.bitquery.mapper import BitqueryEVMMapper
from backend.app.blockchain.exceptions import (
    InvalidAddressError,
    UnsupportedChainError,
    RateLimitError,
    AuthenticationError,
    ProviderTimeoutError,
    ProviderUnavailableError
)
from backend.app.schemas.investigation import InvestigationCreateRequest, InvestigationResponse
from backend.app.services.investigation_service import InvestigationService
from backend.app.api.investigations import get_investigation_service

client = TestClient(app)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "bitquery" / "ethereum"


class MockOfflineProvider(BlockchainProvider):
    """Configurable mock provider for isolated unit testing."""

    def __init__(self, transfers=None, transactions=None, valid_address=True):
        self.transfers_list = transfers or []
        self.transactions_list = transactions or []
        self.valid_address = valid_address

    async def validate_address(self, chain: Chain, address: str) -> AddressValidation:
        if not self.valid_address or address.startswith("0xinvalid"):
            return AddressValidation(
                valid=False,
                normalized_address=address,
                chain=chain,
                reason="Invalid mock address"
            )
        return AddressValidation(
            valid=True,
            normalized_address=address.lower(),
            chain=chain,
            reason="Mock valid"
        )

    async def get_transactions(self, chain: Chain, address: str, **kwargs) -> TransactionPage:
        txs = [tx for tx in self.transactions_list if tx.tx_hash]
        return TransactionPage(transactions=txs, has_more=False)

    async def get_transaction(self, chain: Chain, tx_hash: str) -> NormalizedTransaction | None:
        for tx in self.transactions_list:
            if tx.tx_hash == tx_hash:
                return tx
        return None

    async def get_transfers(self, chain: Chain, address: str, **kwargs) -> TransferPage:
        transfers = [t for t in self.transfers_list if t.from_address.lower() == address.lower() or t.to_address.lower() == address.lower()]
        return TransferPage(transfers=transfers, has_more=False)

    async def get_block(self, chain: Chain, **kwargs):
        return None

    async def get_asset_metadata(self, chain: Chain, asset_id: str):
        return None

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(chains=[Chain.ETHEREUM])


# ============================================================
# 1. Request Validation Tests
# ============================================================

def test_investigation_request_validation():
    # Valid Ethereum request
    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address="0x28C6c06298d514Db089934071355E5743bf21d60",
        max_hops=2,
        max_transactions=50
    )
    assert req.chain == Chain.ETHEREUM
    assert req.max_hops == 2
    assert req.max_transactions == 50

    # Test invalid max_hops (< 1 or > 5)
    with pytest.raises(Exception):
        InvestigationCreateRequest(address="0x28C6c06298d514Db089934071355E5743bf21d60", max_hops=0)
    with pytest.raises(Exception):
        InvestigationCreateRequest(address="0x28C6c06298d514Db089934071355E5743bf21d60", max_hops=6)

    # Test invalid max_transactions (< 1 or > 200)
    with pytest.raises(Exception):
        InvestigationCreateRequest(address="0x28C6c06298d514Db089934071355E5743bf21d60", max_transactions=0)
    with pytest.raises(Exception):
        InvestigationCreateRequest(address="0x28C6c06298d514Db089934071355E5743bf21d60", max_transactions=201)

    # Test empty address validation
    with pytest.raises(Exception):
        InvestigationCreateRequest(address="   ")


def test_investigation_api_http_validation():
    # Invalid max_hops via HTTP endpoint (Pydantic 422 validation error)
    resp = client.post(
        "/api/v1/investigations",
        json={
            "chain": "ethereum",
            "address": "0x28C6c06298d514Db089934071355E5743bf21d60",
            "max_hops": 10,
            "max_transactions": 50
        }
    )
    assert resp.status_code == 422

    # Invalid address length
    resp2 = client.post(
        "/api/v1/investigations",
        json={
            "chain": "ethereum",
            "address": "0x1",
            "max_hops": 1,
            "max_transactions": 50
        }
    )
    assert resp2.status_code == 422


# ============================================================
# 2. Service Orchestration & Response Schema
# ============================================================

@pytest.mark.anyio
async def test_investigation_service_orchestration():
    root = "0x28c6c06298d514db089934071355e5743bf21d60"
    dest1 = "0x4d749d36c8463215a5d7f0e70d2eca71e7741020"

    t1 = NormalizedTransfer(
        transfer_id="ethereum:0xtx1:log_0",
        tx_hash="0xtx1",
        chain=Chain.ETHEREUM,
        from_address=root,
        to_address=dest1,
        asset_type=AssetType.ERC20,
        asset_id="0x3506424f91fd33084466f402d5d97f05f8e3b4af",
        asset_symbol="CHZ",
        raw_amount="952945123120000000000",
        normalized_amount=Decimal("952.94512312"),
        transfer_type=TransferType.TOKEN,
        timestamp=datetime(2026, 9, 28, 11, 55, 47, tzinfo=timezone.utc),
        evidence_ref="bitquery://evm/eth/tx/0xtx1#transfer:log_0"
    )

    tx1 = NormalizedTransaction(
        tx_hash="0xtx1",
        chain=Chain.ETHEREUM,
        timestamp=datetime(2026, 9, 28, 11, 55, 47, tzinfo=timezone.utc),
        status=TransactionStatus.CONFIRMED,
        transfers=[t1],
        provider="mock"
    )

    mock_provider = MockOfflineProvider(transfers=[t1], transactions=[tx1])
    service = InvestigationService(provider=mock_provider)

    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address=root,
        max_hops=1,
        max_transactions=10
    )

    result = await service.investigate(req)

    assert isinstance(result, InvestigationResponse)
    assert result.status == "completed"
    assert result.root_address == root
    assert result.chain == Chain.ETHEREUM
    assert result.investigation_id.startswith("inv_")

    # Summary metrics
    assert result.summary.nodes == 2
    assert result.summary.edges == 1
    assert result.summary.transactions == 1
    assert result.summary.transfers == 1
    assert result.summary.hops == 1

    # Graph checks
    assert result.graph.total_nodes == 2
    assert result.graph.total_edges == 1

    # Root node must be SUSPECT
    suspect_node = next(n for n in result.graph.nodes if n.id == root.lower())
    assert suspect_node.node_type == "SUSPECT"
    assert suspect_node.metadata.get("is_root") is True

    # Edge preservation
    edge = result.graph.edges[0]
    assert edge.transfer_id == "ethereum:0xtx1:log_0"
    assert edge.tx_hash == "0xtx1"
    assert edge.asset_symbol == "CHZ"
    assert edge.amount == Decimal("952.94512312")
    assert isinstance(edge.amount, Decimal)
    assert edge.transfer_type == "TOKEN"
    assert edge.evidence_ref == "bitquery://evm/eth/tx/0xtx1#transfer:log_0"


# ============================================================
# 3. Real Fixture Pipeline Integration Test
# ============================================================

@pytest.mark.anyio
async def test_investigation_service_with_real_fixtures():
    """
    Tests full InvestigationService using mapped transfers from real captured Bitquery fixtures.
    """
    with open(FIXTURES_DIR / "transfers_real.json", "r", encoding="utf-8") as f:
        raw_transfers = json.load(f).get("data", {}).get("EVM", {}).get("Transfers", [])
    
    with open(FIXTURES_DIR / "transaction_real.json", "r", encoding="utf-8") as f:
        raw_txs = json.load(f).get("data", {}).get("EVM", {}).get("Transactions", [])

    mapped_transfers = BitqueryEVMMapper.map_transfers(raw_transfers)
    mapped_txs = [BitqueryEVMMapper.map_transaction(raw_tx, attached_transfers=mapped_transfers) for raw_tx in raw_txs]

    root_wallet = "0x28c6c06298d514db089934071355e5743bf21d60"
    mock_provider = MockOfflineProvider(transfers=mapped_transfers, transactions=mapped_txs)
    service = InvestigationService(provider=mock_provider)

    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address=root_wallet,
        max_hops=1,
        max_transactions=50
    )

    response = await service.investigate(req)

    assert response.status == "completed"
    assert response.summary.nodes >= 2
    assert response.summary.edges >= 1
    assert response.summary.transactions >= 1
    assert response.summary.transfers >= 1

    # Exact Decimal check
    for edge in response.graph.edges:
        assert isinstance(edge.amount, Decimal)
        assert edge.amount > Decimal("0")


# ============================================================
# 4. Empty / Low-Data Wallet Handling
# ============================================================

@pytest.mark.anyio
async def test_investigation_service_empty_wallet_handling():
    """
    Valid wallet with zero on-chain transactions must return a valid completed
    investigation with 1 node (suspect root) and 0 edges without throwing error.
    """
    empty_wallet = "0x000000000000000000000000000000000000dead"
    mock_provider = MockOfflineProvider(transfers=[], transactions=[])
    service = InvestigationService(provider=mock_provider)

    req = InvestigationCreateRequest(
        chain=Chain.ETHEREUM,
        address=empty_wallet,
        max_hops=1,
        max_transactions=50
    )

    result = await service.investigate(req)

    assert result.status == "completed"
    assert result.root_address == empty_wallet.lower()
    assert result.summary.nodes == 1
    assert result.summary.edges == 0
    assert result.summary.transactions == 0
    assert result.summary.transfers == 0
    assert result.summary.hops == 0

    assert len(result.graph.nodes) == 1
    assert result.graph.nodes[0].node_type == "SUSPECT"
    assert result.graph.nodes[0].id == empty_wallet.lower()
    assert len(result.graph.edges) == 0


# ============================================================
# 5. Domain Exception & Error Mapping Tests via HTTP
# ============================================================

def test_api_invalid_address_error_mapping():
    class RejectingProvider(MockOfflineProvider):
        async def validate_address(self, chain, address):
            return AddressValidation(valid=False, normalized_address=address, chain=chain, reason="Invalid checksum")

    app.dependency_overrides[get_investigation_service] = lambda: InvestigationService(provider=RejectingProvider())
    try:
        resp = client.post(
            "/api/v1/investigations",
            json={
                "chain": "ethereum",
                "address": "0xinvalidaddress12345",
                "max_hops": 1,
                "max_transactions": 50
            }
        )
        assert resp.status_code == 400
        assert "Invalid checksum" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_api_rate_limit_error_mapping():
    class RateLimitedProvider(MockOfflineProvider):
        async def validate_address(self, chain, address):
            raise RateLimitError("Rate quota exceeded")

    app.dependency_overrides[get_investigation_service] = lambda: InvestigationService(provider=RateLimitedProvider())
    try:
        resp = client.post(
            "/api/v1/investigations",
            json={
                "chain": "ethereum",
                "address": "0x28C6c06298d514Db089934071355E5743bf21d60",
                "max_hops": 1,
                "max_transactions": 50
            }
        )
        assert resp.status_code == 429
        assert "rate limit" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_api_auth_error_mapping():
    class AuthFailingProvider(MockOfflineProvider):
        async def validate_address(self, chain, address):
            raise AuthenticationError("Bad credentials")

    app.dependency_overrides[get_investigation_service] = lambda: InvestigationService(provider=AuthFailingProvider())
    try:
        resp = client.post(
            "/api/v1/investigations",
            json={
                "chain": "ethereum",
                "address": "0x28C6c06298d514Db089934071355E5743bf21d60",
                "max_hops": 1,
                "max_transactions": 50
            }
        )
        assert resp.status_code == 502
        assert "authentication" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_api_provider_timeout_error_mapping():
    class TimeoutProvider(MockOfflineProvider):
        async def validate_address(self, chain, address):
            raise ProviderTimeoutError("Query timed out")

    app.dependency_overrides[get_investigation_service] = lambda: InvestigationService(provider=TimeoutProvider())
    try:
        resp = client.post(
            "/api/v1/investigations",
            json={
                "chain": "ethereum",
                "address": "0x28C6c06298d514Db089934071355E5743bf21d60",
                "max_hops": 1,
                "max_transactions": 50
            }
        )
        assert resp.status_code == 504
        assert "timed out" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


# ============================================================
# 6. Zero Provider Leakage Verification
# ============================================================

def test_api_response_zero_provider_leakage():
    """
    Verifies that the serialized investigation response contains no GraphQL text,
    tokens, or internal Python object representations.
    """
    root = "0x28c6c06298d514db089934071355e5743bf21d60"
    dest = "0x4d749d36c8463215a5d7f0e70d2eca71e7741020"

    t = NormalizedTransfer(
        transfer_id="ethereum:0xtx1:0",
        tx_hash="0xtx1",
        chain=Chain.ETHEREUM,
        from_address=root,
        to_address=dest,
        asset_symbol="ETH",
        normalized_amount=Decimal("1.0"),
        transfer_type=TransferType.NATIVE,
        timestamp=datetime(2026, 9, 28, 12, 0, 0, tzinfo=timezone.utc),
        evidence_ref="bitquery://evm/eth/tx/0xtx1#transfer:0"
    )
    tx = NormalizedTransaction(
        tx_hash="0xtx1",
        chain=Chain.ETHEREUM,
        timestamp=datetime(2026, 9, 28, 12, 0, 0, tzinfo=timezone.utc),
        status=TransactionStatus.CONFIRMED,
        transfers=[t],
        provider="mock"
    )

    app.dependency_overrides[get_investigation_service] = lambda: InvestigationService(
        provider=MockOfflineProvider(transfers=[t], transactions=[tx])
    )
    try:
        resp = client.post(
            "/api/v1/investigations",
            json={
                "chain": "ethereum",
                "address": root,
                "max_hops": 1,
                "max_transactions": 10
            }
        )
        assert resp.status_code == 200
        raw_text = resp.text

        # Zero leakage assertions
        assert "query {" not in raw_text
        assert "query GetTransfers" not in raw_text
        assert "BITQUERY_ACCESS_TOKEN" not in raw_text
        assert "Bearer " not in raw_text
        assert "<networkx." not in raw_text
        assert "<class " not in raw_text
    finally:
        app.dependency_overrides.clear()

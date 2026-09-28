# tests/unit/test_collector.py
from datetime import datetime
from decimal import Decimal
import pytest
from backend.app.blockchain.models.enums import Chain, TransferDirection, TransactionStatus, TransactionType, AssetType, TransferType
from backend.app.blockchain.models.provider import AddressValidation, ProviderCapabilities
from backend.app.blockchain.models.pagination import TransactionPage, TransferPage
from backend.app.blockchain.models.transaction import NormalizedTransaction
from backend.app.blockchain.models.transfer import NormalizedTransfer
from backend.app.blockchain.providers.base import BlockchainProvider
from backend.app.blockchain.ingestion.collector import TransactionCollector

class MockBlockchainProvider(BlockchainProvider):
    """Mock provider for unit testing the TransactionCollector independently."""

    def __init__(self):
        self.addresses = {
            "0xroot": [
                NormalizedTransfer(
                    transfer_id="tx1_0",
                    tx_hash="0xtx1",
                    chain=Chain.ETHEREUM,
                    from_address="0xroot",
                    to_address="0xhop1",
                    asset_type=AssetType.NATIVE,
                    asset_id="ETH",
                    asset_symbol="ETH",
                    raw_amount="10000000000000000000",
                    normalized_amount=Decimal("10"),
                    transfer_type=TransferType.NATIVE,
                    transfer_index=0,
                    timestamp=datetime(2026, 3, 14, 10, 0, 0)
                )
            ],
            "0xhop1": [
                NormalizedTransfer(
                    transfer_id="tx2_0",
                    tx_hash="0xtx2",
                    chain=Chain.ETHEREUM,
                    from_address="0xhop1",
                    to_address="0xhop2",
                    asset_type=AssetType.NATIVE,
                    asset_id="ETH",
                    asset_symbol="ETH",
                    raw_amount="5000000000000000000",
                    normalized_amount=Decimal("5"),
                    transfer_type=TransferType.NATIVE,
                    transfer_index=0,
                    timestamp=datetime(2026, 3, 14, 10, 30, 0)
                ),
                # Cycle transfer pointing back to root
                NormalizedTransfer(
                    transfer_id="tx3_0",
                    tx_hash="0xtx3",
                    chain=Chain.ETHEREUM,
                    from_address="0xhop1",
                    to_address="0xroot",
                    asset_type=AssetType.NATIVE,
                    asset_id="ETH",
                    asset_symbol="ETH",
                    raw_amount="1000000000000000000",
                    normalized_amount=Decimal("1"),
                    transfer_type=TransferType.NATIVE,
                    transfer_index=0,
                    timestamp=datetime(2026, 3, 14, 10, 35, 0)
                )
            ],
            "0xhop2": []
        }

        self.transactions = {
            "0xtx1": NormalizedTransaction(
                tx_hash="0xtx1",
                chain=Chain.ETHEREUM,
                timestamp=datetime(2026, 3, 14, 10, 0, 0),
                status=TransactionStatus.CONFIRMED,
                provider="MOCK"
            ),
            "0xtx2": NormalizedTransaction(
                tx_hash="0xtx2",
                chain=Chain.ETHEREUM,
                timestamp=datetime(2026, 3, 14, 10, 30, 0),
                status=TransactionStatus.CONFIRMED,
                provider="MOCK"
            ),
            "0xtx3": NormalizedTransaction(
                tx_hash="0xtx3",
                chain=Chain.ETHEREUM,
                timestamp=datetime(2026, 3, 14, 10, 35, 0),
                status=TransactionStatus.CONFIRMED,
                provider="MOCK"
            )
        }

    async def validate_address(self, chain: Chain, address: str) -> AddressValidation:
        return AddressValidation(
            valid=True,
            normalized_address=address.lower(),
            chain=chain,
            reason="Mock valid"
        )

    async def get_transactions(self, chain: Chain, address: str, **kwargs) -> TransactionPage:
        return TransactionPage(transactions=[], has_more=False)

    async def get_transaction(self, chain: Chain, tx_hash: str) -> NormalizedTransaction | None:
        return self.transactions.get(tx_hash)

    async def get_transfers(self, chain: Chain, address: str, **kwargs) -> TransferPage:
        transfers = self.addresses.get(address.lower(), [])
        return TransferPage(transfers=transfers, has_more=False)

    async def get_block(self, chain: Chain, **kwargs):
        return None

    async def get_asset_metadata(self, chain: Chain, asset_id: str):
        return None

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(chains=[Chain.ETHEREUM])


@pytest.mark.anyio
async def test_collector_cycle_prevention_and_traversal():
    mock_provider = MockBlockchainProvider()
    collector = TransactionCollector(provider=mock_provider)

    batch = await collector.collect_case_transactions(
        case_id="CASE-TEST-COLLECTOR",
        suspect_wallet="0xroot",
        chain=Chain.ETH,
        max_hops=3,
        direction=TransferDirection.OUTGOING
    )

    assert batch.case_id == "CASE-TEST-COLLECTOR"
    assert batch.suspect_address == "0xroot"
    # Should ingest tx1 and tx2; tx3 (pointing back to root) should be pruned by cycle prevention
    assert len(batch.transactions) == 2
    tx_hashes = {t.tx_hash for t in batch.transactions}
    assert "0xtx1" in tx_hashes
    assert "0xtx2" in tx_hashes

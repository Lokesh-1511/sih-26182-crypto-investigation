# tests/unit/test_providers.py
import pytest
from datetime import datetime
from backend.app.blockchain.models.enums import Chain, TransferDirection
from backend.app.blockchain.models.provider import AddressValidation, ProviderCapabilities
from backend.app.blockchain.models.pagination import TransactionPage, TransferPage
from backend.app.blockchain.providers.fixture_provider import FixtureBlockchainProvider
from backend.app.blockchain.providers.bitquery_provider import BitqueryProvider
from backend.app.blockchain.providers.rpc_provider import RpcProvider
from backend.app.blockchain.exceptions import ProviderUnavailableError

@pytest.mark.anyio
async def test_fixture_provider_interface_compliance():
    provider = FixtureBlockchainProvider()

    # Capabilities
    caps = provider.capabilities()
    assert isinstance(caps, ProviderCapabilities)
    assert Chain.ETHEREUM in caps.chains
    assert Chain.BITCOIN in caps.chains
    assert Chain.TRON in caps.chains

    # Validate address
    val = await provider.validate_address(Chain.ETH, "0x71C83e20e8F468a3E282241F8C936f4521487439")
    assert isinstance(val, AddressValidation)
    assert val.valid is True

    # Get transactions
    tx_page = await provider.get_transactions(
        chain=Chain.ETH,
        address="0x71C83e20e8F468a3E282241F8C936f4521487439",
        limit=10
    )
    assert isinstance(tx_page, TransactionPage)
    assert len(tx_page.transactions) > 0

    # Get single transaction
    first_hash = tx_page.transactions[0].tx_hash
    tx_detail = await provider.get_transaction(Chain.ETH, first_hash)
    assert tx_detail is not None
    assert tx_detail.tx_hash == first_hash

    # Get transfers
    transfer_page = await provider.get_transfers(
        chain=Chain.ETH,
        address="0x71C83e20e8F468a3E282241F8C936f4521487439",
        direction=TransferDirection.OUTGOING
    )
    assert isinstance(transfer_page, TransferPage)
    assert len(transfer_page.transfers) > 0

    # Get block
    block = await provider.get_block(Chain.ETH, block_number=19482010)
    assert block is not None
    assert block.block_number == 19482010

    # Get asset metadata
    asset = await provider.get_asset_metadata(Chain.ETH, "ETH")
    assert asset is not None
    assert asset.symbol == "ETH"


@pytest.mark.anyio
async def test_fixture_provider_pagination():
    provider = FixtureBlockchainProvider()

    # Query with small limit to test pagination cursor
    page1 = await provider.get_transfers(
        chain=Chain.ETH,
        address="0x3a9B552f4c91E606132D9eD9D5FaD79f18B57062",
        limit=2
    )
    assert isinstance(page1, TransferPage)

    if page1.has_more and page1.next_cursor:
        page2 = await provider.get_transfers(
            chain=Chain.ETH,
            address="0x3a9B552f4c91E606132D9eD9D5FaD79f18B57062",
            cursor=page1.next_cursor,
            limit=2
        )
        assert isinstance(page2, TransferPage)
        assert page1.transfers[0].transfer_id != page2.transfers[0].transfer_id


@pytest.mark.anyio
async def test_bitquery_provider_skeleton_raises_unavailable():
    provider = BitqueryProvider(api_key="test_dummy_key")
    caps = provider.capabilities()
    assert isinstance(caps, ProviderCapabilities)

    # Address validation runs locally
    val = await provider.validate_address(Chain.ETH, "0xd8da6bf26964af9d7eed9e03e53415d37aa96045")
    assert val.valid is True

    # Unimplemented live methods raise ProviderUnavailableError
    with pytest.raises(ProviderUnavailableError):
        await provider.get_transactions(Chain.ETH, "0xd8da6bf26964af9d7eed9e03e53415d37aa96045")

    with pytest.raises(ProviderUnavailableError):
        await provider.get_transfers(Chain.ETH, "0xd8da6bf26964af9d7eed9e03e53415d37aa96045")


@pytest.mark.anyio
async def test_rpc_provider_skeleton_raises_unavailable():
    provider = RpcProvider()
    caps = provider.capabilities()
    assert isinstance(caps, ProviderCapabilities)

    with pytest.raises(ProviderUnavailableError):
        await provider.get_transactions(Chain.ETH, "0xd8da6bf26964af9d7eed9e03e53415d37aa96045")

# tests/integration/test_bitquery_live.py
import os
import asyncio
import pytest
from dotenv import load_dotenv

load_dotenv()

from backend.app.blockchain.models.enums import Chain, TransferDirection
from backend.app.blockchain.providers.bitquery.provider import BitqueryProvider
from backend.app.blockchain.ingestion.collector import TransactionCollector

# Skip unless explicitly enabled with RUN_LIVE_BITQUERY=1 and token is available
pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_BITQUERY") != "1" or not os.getenv("BITQUERY_ACCESS_TOKEN"),
    reason="Live Bitquery test is opt-in. Set RUN_LIVE_BITQUERY=1 and BITQUERY_ACCESS_TOKEN to execute live queries."
)

@pytest.mark.anyio
async def test_bitquery_live_ethereum_wallet_trace():
    token = os.environ["BITQUERY_ACCESS_TOKEN"]
    provider = BitqueryProvider(access_token=token)

    # Active Ethereum wallet with guaranteed recent activity in realtime rolling window
    target_wallet = "0x28C6c06298d514Db089934071355E5743bf21d60"

    # 1. Address Validation
    val = await provider.validate_address(Chain.ETHEREUM, target_wallet)
    assert val.valid is True

    # 2. Query Transfers in realtime window
    transfer_page = await provider.get_transfers(
        chain=Chain.ETHEREUM,
        address=target_wallet,
        direction=TransferDirection.ANY,
        limit=5
    )
    assert len(transfer_page.transfers) > 0
    first_transfer = transfer_page.transfers[0]
    assert first_transfer.chain == Chain.ETHEREUM
    assert first_transfer.tx_hash.startswith("0x")
    assert first_transfer.normalized_amount is not None
    assert first_transfer.evidence_ref.startswith("bitquery://evm/eth/tx/")

    await asyncio.sleep(0.5)

    # 3. Query Transactions in realtime window
    tx_page = await provider.get_transactions(
        chain=Chain.ETHEREUM,
        address=target_wallet,
        direction=TransferDirection.ANY,
        limit=5
    )
    assert len(tx_page.transactions) > 0
    first_tx = tx_page.transactions[0]
    assert first_tx.chain == Chain.ETHEREUM
    assert first_tx.tx_hash.startswith("0x")

    await asyncio.sleep(0.5)

    # 4. Direct Transaction Lookup
    lookup_hash = first_tx.tx_hash
    tx_detail = await provider.get_transaction(Chain.ETHEREUM, lookup_hash)
    assert tx_detail is not None
    assert tx_detail.tx_hash.lower() == lookup_hash.lower()
    assert tx_detail.chain == Chain.ETHEREUM
    assert tx_detail.provider == "bitquery"

    await asyncio.sleep(0.5)

    # 5. Collector Ingestion
    collector = TransactionCollector(provider=provider)
    batch = await collector.collect_case_transactions(
        case_id="CASE-LIVE-BITQUERY",
        suspect_wallet=target_wallet,
        chain=Chain.ETHEREUM,
        max_hops=1,
        max_transactions=2,
        page_limit=2
    )
    assert batch.total_transactions > 0


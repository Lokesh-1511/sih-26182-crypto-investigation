# backend/app/blockchain/providers/bitquery/provider.py
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from ..base import BlockchainProvider
from ...models.enums import Chain, TransferDirection, AssetType
from ...models.provider import AddressValidation, ProviderCapabilities
from ...models.pagination import TransactionPage, TransferPage
from ...models.transaction import NormalizedTransaction
from ...models.transfer import NormalizedTransfer
from ...models.block import BlockMetadata
from ...models.asset import AssetMetadata
from ...exceptions import (
    UnsupportedChainError,
    InvalidAddressError,
    ProviderResponseError,
)
from ...validation.validator import MultiChainValidator

from .client import BitqueryClient
from .pagination import encode_cursor, decode_cursor
from .mapper import BitqueryEVMMapper
from .queries import (
    build_transactions_query,
    build_transfers_query,
    ETHEREUM_TRANSACTIONS_OUTGOING_QUERY,
    ETHEREUM_TRANSACTIONS_INCOMING_QUERY,
    ETHEREUM_TRANSACTIONS_ANY_QUERY,
    ETHEREUM_TRANSACTION_BY_HASH_QUERY,
    ETHEREUM_TRANSFERS_OUTGOING_QUERY,
    ETHEREUM_TRANSFERS_INCOMING_QUERY,
    ETHEREUM_TRANSFERS_ANY_QUERY,
    ETHEREUM_TRANSFERS_BY_TX_HASHES_QUERY,
    ETHEREUM_BLOCK_BY_NUMBER_QUERY,
    ETHEREUM_BLOCK_BY_HASH_QUERY,
    ETHEREUM_ASSET_METADATA_QUERY,
)

class BitqueryProvider(BlockchainProvider):
    """
    Production Bitquery V2 Blockchain Provider for Ethereum Mainnet.
    Consumes Bitquery V2 GraphQL realtime dataset to deliver normalized transactions,
    transfers, block metadata, and token assets over a rolling recent window.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        access_token: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        max_retries: Optional[int] = None,
        client: Optional[BitqueryClient] = None
    ):
        self.client = client or BitqueryClient(
            api_url=api_url,
            access_token=access_token,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries
        )

    def _ensure_ethereum(self, chain: Chain) -> None:
        if chain not in (Chain.ETHEREUM, Chain.ETH):
            raise UnsupportedChainError(
                f"BitqueryProvider currently implements Ethereum Mainnet only. Received unsupported chain: {chain}"
            )

    async def validate_address(
        self,
        chain: Chain,
        address: str
    ) -> AddressValidation:
        self._ensure_ethereum(chain)
        return MultiChainValidator.validate(address, Chain.ETHEREUM)

    async def get_transactions(
        self,
        chain: Chain,
        address: str,
        direction: TransferDirection = TransferDirection.ANY,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        cursor: Optional[str] = None,
        limit: int = 100
    ) -> TransactionPage:
        self._ensure_ethereum(chain)
        
        val = MultiChainValidator.validate(address, Chain.ETHEREUM)
        if not val.valid:
            raise InvalidAddressError(f"Invalid Ethereum address: {address} ({val.reason})")

        normalized_addr = val.normalized_address
        offset = decode_cursor(cursor, kind="transactions")
        fetch_count = limit + 1

        has_since = start_time is not None
        has_till = end_time is not None
        query = build_transactions_query(
            direction=direction,
            has_since=has_since,
            has_till=has_till
        )

        variables: Dict[str, Any] = {
            "address": normalized_addr,
            "limit": fetch_count,
            "offset": offset
        }
        if has_since:
            variables["since"] = start_time.isoformat()
        if has_till:
            variables["till"] = end_time.isoformat()

        response_data = await self.client.execute_query(query, variables)
        evm_data = response_data.get("data", {}).get("EVM", {}) or {}
        raw_txs = evm_data.get("Transactions", []) or []

        has_more = len(raw_txs) > limit
        paged_raw_txs = raw_txs[:limit]
        next_cursor = encode_cursor(offset + limit, kind="transactions") if has_more else None

        if not paged_raw_txs:
            return TransactionPage(transactions=[], next_cursor=None, has_more=False)

        # Batch query transfers for the page of transactions (avoids N+1 query problem)
        tx_hashes = [
            tx.get("Transaction", {}).get("Hash")
            for tx in paged_raw_txs
            if tx.get("Transaction", {}).get("Hash")
        ]

        transfers_by_tx: Dict[str, List[NormalizedTransfer]] = {h.lower(): [] for h in tx_hashes}
        if tx_hashes:
            try:
                transfer_resp = await self.client.execute_query(
                    ETHEREUM_TRANSFERS_BY_TX_HASHES_QUERY,
                    {"txHashes": tx_hashes}
                )
                raw_transfers = transfer_resp.get("data", {}).get("EVM", {}).get("Transfers", []) or []
                mapped_transfers = BitqueryEVMMapper.map_transfers(raw_transfers)
                for norm_t in mapped_transfers:
                    t_hash = norm_t.tx_hash.lower()
                    if t_hash in transfers_by_tx:
                        transfers_by_tx[t_hash].append(norm_t)
            except Exception:
                # If batch transfer query fails, gracefully proceed with native transfer inference
                pass

        normalized_txs: List[NormalizedTransaction] = []
        for raw_tx in paged_raw_txs:
            tx_h = raw_tx.get("Transaction", {}).get("Hash", "").lower()
            attached_t = transfers_by_tx.get(tx_h, [])
            norm_tx = BitqueryEVMMapper.map_transaction(raw_tx, attached_transfers=attached_t)
            normalized_txs.append(norm_tx)

        return TransactionPage(
            transactions=normalized_txs,
            next_cursor=next_cursor,
            has_more=has_more
        )

    async def get_transaction(
        self,
        chain: Chain,
        tx_hash: str
    ) -> Optional[NormalizedTransaction]:
        self._ensure_ethereum(chain)
        if not tx_hash or not isinstance(tx_hash, str) or not tx_hash.startswith("0x"):
            raise InvalidAddressError(f"Invalid Ethereum transaction hash: {tx_hash}")

        # 1. Fetch transaction container
        response_data = await self.client.execute_query(
            ETHEREUM_TRANSACTION_BY_HASH_QUERY,
            {"txHash": tx_hash}
        )
        raw_txs = response_data.get("data", {}).get("EVM", {}).get("Transactions", []) or []
        if not raw_txs:
            return None

        raw_tx = raw_txs[0]

        # 2. Fetch associated transfers
        attached_transfers: List[NormalizedTransfer] = []
        try:
            transfer_resp = await self.client.execute_query(
                ETHEREUM_TRANSFERS_BY_TX_HASHES_QUERY,
                {"txHashes": [tx_hash]}
            )
            raw_transfers = transfer_resp.get("data", {}).get("EVM", {}).get("Transfers", []) or []
            attached_transfers = BitqueryEVMMapper.map_transfers(raw_transfers)
        except Exception:
            pass

        return BitqueryEVMMapper.map_transaction(raw_tx, attached_transfers=attached_transfers)

    async def get_transfers(
        self,
        chain: Chain,
        address: str,
        direction: TransferDirection = TransferDirection.ANY,
        asset_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        cursor: Optional[str] = None,
        limit: int = 100
    ) -> TransferPage:
        self._ensure_ethereum(chain)

        val = MultiChainValidator.validate(address, Chain.ETHEREUM)
        if not val.valid:
            raise InvalidAddressError(f"Invalid Ethereum address: {address} ({val.reason})")

        normalized_addr = val.normalized_address
        offset = decode_cursor(cursor, kind="transfers")
        fetch_count = limit + 1

        # Token contract extraction if asset_id is provided
        contract_filter: Optional[str] = None
        if asset_id:
            asset_clean = asset_id.strip()
            if asset_clean.lower() in ("eth", "ether", "native"):
                contract_filter = None
            elif asset_clean.startswith("ethereum:"):
                contract_filter = asset_clean.split(":", 1)[1]
            elif asset_clean.startswith("0x"):
                contract_filter = asset_clean

        has_since = start_time is not None
        has_till = end_time is not None
        has_contract = contract_filter is not None

        query = build_transfers_query(
            direction=direction,
            has_since=has_since,
            has_till=has_till,
            has_contract=has_contract
        )

        variables: Dict[str, Any] = {
            "address": normalized_addr,
            "limit": fetch_count,
            "offset": offset
        }
        if has_since:
            variables["since"] = start_time.isoformat()
        if has_till:
            variables["till"] = end_time.isoformat()
        if has_contract:
            variables["contract"] = contract_filter

        response_data = await self.client.execute_query(query, variables)
        evm_data = response_data.get("data", {}).get("EVM", {}) or {}
        raw_transfers = evm_data.get("Transfers", []) or []

        has_more = len(raw_transfers) > limit
        paged_raw = raw_transfers[:limit]
        next_cursor = encode_cursor(offset + limit, kind="transfers") if has_more else None

        normalized_transfers = BitqueryEVMMapper.map_transfers(paged_raw)

        return TransferPage(
            transfers=normalized_transfers,
            next_cursor=next_cursor,
            has_more=has_more
        )

    async def get_block(
        self,
        chain: Chain,
        block_number: Optional[int] = None,
        block_hash: Optional[str] = None
    ) -> Optional[BlockMetadata]:
        self._ensure_ethereum(chain)

        if block_number is None and not block_hash:
            raise ProviderResponseError("Either block_number or block_hash must be provided to get_block.")

        if block_number is not None:
            query = ETHEREUM_BLOCK_BY_NUMBER_QUERY
            variables = {"blockNumber": str(block_number)}
        else:
            query = ETHEREUM_BLOCK_BY_HASH_QUERY
            variables = {"blockHash": str(block_hash)}

        response_data = await self.client.execute_query(query, variables)
        raw_blocks = response_data.get("data", {}).get("EVM", {}).get("Blocks", []) or []
        if not raw_blocks:
            return None

        return BitqueryEVMMapper.map_block(raw_blocks[0])

    async def get_asset_metadata(
        self,
        chain: Chain,
        asset_id: str
    ) -> Optional[AssetMetadata]:
        self._ensure_ethereum(chain)

        clean_id = asset_id.strip()
        if clean_id.lower() in ("eth", "ether"):
            return AssetMetadata(
                asset_id="ETH",
                chain=Chain.ETHEREUM,
                asset_type=AssetType.NATIVE,
                symbol="ETH",
                name="Ether",
                decimals=18,
                token_contract=None,
                verified=True
            )

        contract_addr = clean_id.split(":", 1)[1] if clean_id.startswith("ethereum:") else clean_id
        if not contract_addr.startswith("0x") or len(contract_addr) != 42:
            return None

        response_data = await self.client.execute_query(
            ETHEREUM_ASSET_METADATA_QUERY,
            {"contract": contract_addr}
        )
        raw_transfers = response_data.get("data", {}).get("EVM", {}).get("Transfers", []) or []
        if not raw_transfers:
            return None

        return BitqueryEVMMapper.map_asset_metadata(raw_transfers[0], contract_addr)

    def capabilities(self) -> ProviderCapabilities:
        """
        Capabilities of this BitqueryProvider instance for Ethereum Mainnet.
        Note: Queries Bitquery realtime dataset (rolling window), so supports_historical_data is False.
        """
        return ProviderCapabilities(
            chains=[Chain.ETHEREUM],
            supports_transactions=True,
            supports_transfers=True,
            supports_token_metadata=True,
            supports_blocks=True,
            supports_historical_data=False,
            supports_internal_transfers=False
        )

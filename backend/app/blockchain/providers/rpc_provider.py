# backend/app/blockchain/providers/rpc_provider.py
from datetime import datetime
from typing import Optional, Dict

from .base import BlockchainProvider
from ..models.enums import Chain, TransferDirection
from ..models.provider import AddressValidation, ProviderCapabilities
from ..models.pagination import TransactionPage, TransferPage
from ..models.transaction import NormalizedTransaction
from ..models.block import BlockMetadata
from ..models.asset import AssetMetadata
from ..exceptions import ProviderUnavailableError
from ..validation.validator import MultiChainValidator

class RpcProvider(BlockchainProvider):
    """
    Direct Node JSON-RPC Provider skeleton (EVM eth_*, Bitcoin bitcoind RPC, Tron java-tron RPC).
    Serves as low-level raw verification fallback.
    """

    def __init__(self, rpc_endpoints: Optional[Dict[Chain, str]] = None):
        self.rpc_endpoints = rpc_endpoints or {}

    async def validate_address(
        self,
        chain: Chain,
        address: str
    ) -> AddressValidation:
        return MultiChainValidator.validate(address, chain)

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
        # TODO: Implement direct JSON-RPC log scanning / mempool scanning in next phase
        raise ProviderUnavailableError(
            "Direct node RPC provider implementation is scheduled for subsequent phase."
        )

    async def get_transaction(
        self,
        chain: Chain,
        tx_hash: str
    ) -> Optional[NormalizedTransaction]:
        # TODO: Implement eth_getTransactionByHash / getrawtransaction RPC calls in next phase
        raise ProviderUnavailableError(
            "Direct node RPC provider implementation is scheduled for subsequent phase."
        )

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
        # TODO: Implement eth_getLogs / filter transfer event scanning in next phase
        raise ProviderUnavailableError(
            "Direct node RPC provider implementation is scheduled for subsequent phase."
        )

    async def get_block(
        self,
        chain: Chain,
        block_number: Optional[int] = None,
        block_hash: Optional[str] = None
    ) -> Optional[BlockMetadata]:
        # TODO: Implement eth_getBlockByNumber / getblock RPC calls in next phase
        raise ProviderUnavailableError(
            "Direct node RPC provider implementation is scheduled for subsequent phase."
        )

    async def get_asset_metadata(
        self,
        chain: Chain,
        asset_id: str
    ) -> Optional[AssetMetadata]:
        # TODO: Implement ERC-20 symbol(), decimals(), name() RPC eth_call in next phase
        raise ProviderUnavailableError(
            "Direct node RPC provider implementation is scheduled for subsequent phase."
        )

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            chains=[Chain.BITCOIN, Chain.ETHEREUM, Chain.BNB, Chain.POLYGON, Chain.TRON],
            supports_transactions=True,
            supports_transfers=True,
            supports_token_metadata=True,
            supports_blocks=True,
            supports_historical_data=False,
            supports_internal_transfers=False
        )

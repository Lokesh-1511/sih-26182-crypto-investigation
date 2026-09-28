# backend/app/blockchain/providers/base.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from ..models.enums import Chain, TransferDirection
from ..models.provider import AddressValidation, ProviderCapabilities
from ..models.pagination import TransactionPage, TransferPage
from ..models.transaction import NormalizedTransaction
from ..models.block import BlockMetadata
from ..models.asset import AssetMetadata

class BlockchainProvider(ABC):
    """
    Vendor-agnostic abstract interface for blockchain intelligence and data providers.
    All downstream components (ingestion, graph, attribution, risk) interact exclusively
    with this contract.
    """

    @abstractmethod
    async def validate_address(
        self,
        chain: Chain,
        address: str
    ) -> AddressValidation:
        """Validate address syntax and cryptographic checksum for target blockchain."""
        pass

    @abstractmethod
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
        """Fetch paginated normalized transactions for target address."""
        pass

    @abstractmethod
    async def get_transaction(
        self,
        chain: Chain,
        tx_hash: str
    ) -> Optional[NormalizedTransaction]:
        """Fetch single normalized transaction by on-chain hash."""
        pass

    @abstractmethod
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
        """Fetch paginated normalized asset transfers (native coins and tokens) for address."""
        pass

    @abstractmethod
    async def get_block(
        self,
        chain: Chain,
        block_number: Optional[int] = None,
        block_hash: Optional[str] = None
    ) -> Optional[BlockMetadata]:
        """Fetch block header and confirmation metadata."""
        pass

    @abstractmethod
    async def get_asset_metadata(
        self,
        chain: Chain,
        asset_id: str
    ) -> Optional[AssetMetadata]:
        """Fetch token or coin metadata (symbol, name, decimals, contract address)."""
        pass

    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """Report features and chains supported by this provider."""
        pass

# backend/app/blockchain/adapters/base.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ...schemas.wallet import Chain
from ...schemas.transaction import NormalizedTransaction, NormalizedTransfer

class BlockchainProvider(ABC):
    """
    Abstract interface for blockchain data providers.
    Enables pluggable data sources: cached offline fixtures or configured live APIs.
    """

    @abstractmethod
    def get_wallet_transactions(
        self, address: str, chain: Chain, limit: int = 50
    ) -> List[NormalizedTransaction]:
        """Fetch all historical transactions involving the specified wallet address."""
        pass

    @abstractmethod
    def get_transaction(
        self, tx_id: str, chain: Chain
    ) -> Optional[NormalizedTransaction]:
        """Fetch single transaction by on-chain hash."""
        pass

    @abstractmethod
    def get_transfers(
        self, address: str, chain: Chain
    ) -> List[NormalizedTransfer]:
        """Fetch normalized transfer events (native coins and tokens) for address."""
        pass

    @abstractmethod
    def get_block(
        self, block_number: int, chain: Chain
    ) -> Optional[Dict[str, Any]]:
        """Fetch block header and metadata."""
        pass

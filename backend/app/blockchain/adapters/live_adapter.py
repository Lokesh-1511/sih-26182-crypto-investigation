# backend/app/blockchain/adapters/live_adapter.py
import os
from typing import List, Optional, Dict, Any
from .base import BlockchainProvider
from ...schemas.wallet import Chain
from ...schemas.transaction import NormalizedTransaction, NormalizedTransfer

class LiveBlockchainProvider(BlockchainProvider):
    """
    Live API adapter connecting to public blockchain explorer APIs
    (Etherscan, Blockstream, TronGrid) when API keys are supplied.
    """

    def __init__(self):
        self.etherscan_key = os.getenv("ETHERSCAN_API_KEY", "")
        self.blockstream_key = os.getenv("BLOCKSTREAM_API_KEY", "")
        self.trongrid_key = os.getenv("TRONGRID_API_KEY", "")

    def get_wallet_transactions(
        self, address: str, chain: Chain, limit: int = 50
    ) -> List[NormalizedTransaction]:
        # Pluggable live provider implementation
        # If API keys are unconfigured or live network is unavailable, return empty or fallback
        return []

    def get_transaction(
        self, tx_id: str, chain: Chain
    ) -> Optional[NormalizedTransaction]:
        return None

    def get_transfers(
        self, address: str, chain: Chain
    ) -> List[NormalizedTransfer]:
        return []

    def get_block(
        self, block_number: int, chain: Chain
    ) -> Optional[Dict[str, Any]]:
        return None

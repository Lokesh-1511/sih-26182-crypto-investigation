# backend/app/blockchain/providers/factory.py
import os
from typing import Optional
from .base import BlockchainProvider
from .bitquery_provider import BitqueryProvider
from .fixture_provider import FixtureBlockchainProvider
from .rpc_provider import RpcProvider
from ..models.enums import Chain

class ProviderFactory:
    """
    Resolves the appropriate BlockchainProvider implementation based on
    system environment configurations (DATA_SOURCE_MODE, BITQUERY_ACCESS_TOKEN).
    """

    @classmethod
    def get_provider(
        cls,
        chain: Optional[Chain] = None,
        mode_override: Optional[str] = None
    ) -> BlockchainProvider:
        mode = (mode_override or os.getenv("DATA_SOURCE_MODE", "OFFLINE_FIXTURE")).upper()
        token = os.getenv("BITQUERY_ACCESS_TOKEN", "").strip()

        # If live Bitquery mode requested and token is present, use BitqueryProvider
        if mode in ("LIVE", "LIVE_BITQUERY", "BITQUERY") and token:
            return BitqueryProvider(access_token=token)

        # Default to FixtureBlockchainProvider for deterministic/offline environments
        return FixtureBlockchainProvider()

# backend/app/intelligence/resolver.py
from typing import List, Dict, Optional
from .models import EntityResolution, ResolutionStatus
from .providers.base import AddressIntelligenceProvider
from .providers.registry import LocalRegistryProvider

class EntityResolver:
    """
    Coordinates entity resolution across discovered blockchain addresses.
    Enforces deduplication, chain-aware address normalization, and safety lookup limits.
    """

    def __init__(self, provider: Optional[AddressIntelligenceProvider] = None, max_lookup_limit: int = 500):
        self.provider = provider or LocalRegistryProvider()
        self.max_lookup_limit = max_lookup_limit

    async def resolve_address(self, chain: str, address: str) -> EntityResolution:
        """Resolves a single address via the configured intelligence provider."""
        return await self.provider.resolve_address(chain=chain, address=address)

    async def resolve_addresses(self, chain: str, addresses: List[str]) -> Dict[str, EntityResolution]:
        """
        Deduplicates and batch-resolves a list of discovered addresses,
        respecting the safety lookup limit.
        """
        # 1. Deduplicate addresses preserving order
        unique_addresses: List[str] = []
        seen = set()
        for addr in addresses:
            addr_clean = str(addr).strip()
            # Normalize for deduplication key
            key = addr_clean.lower() if chain.lower() in ("eth", "ethereum", "polygon", "arbitrum", "bsc") else addr_clean
            if key and key not in seen:
                seen.add(key)
                unique_addresses.append(addr_clean)

        # 2. Enforce bounded lookups
        bounded_list = unique_addresses[:self.max_lookup_limit]

        # 3. Resolve via provider
        return await self.provider.resolve_addresses(chain=chain, addresses=bounded_list)

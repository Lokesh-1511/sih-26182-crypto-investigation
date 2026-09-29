# backend/app/intelligence/providers/base.py
from abc import ABC, abstractmethod
from typing import List, Dict
from ..models import EntityResolution

class AddressIntelligenceProvider(ABC):
    """
    Abstract provider interface for address intelligence, entity resolution,
    and VASP classification. Decouples application logic from specific local registries
    or external intelligence services.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier for this intelligence provider."""
        pass

    @abstractmethod
    async def resolve_address(self, chain: str, address: str) -> EntityResolution:
        """
        Resolves entity metadata for a single blockchain address.
        Returns an EntityResolution with RESOLVED, NOT_FOUND, or AMBIGUOUS status.
        """
        pass

    async def resolve_addresses(self, chain: str, addresses: List[str]) -> Dict[str, EntityResolution]:
        """
        Resolves entity metadata for multiple addresses in batch.
        Default implementation calls resolve_address sequentially; providers may override for optimized batching.
        """
        results: Dict[str, EntityResolution] = {}
        for addr in addresses:
            results[addr] = await self.resolve_address(chain, addr)
        return results

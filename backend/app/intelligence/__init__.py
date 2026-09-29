# backend/app/intelligence/__init__.py
from .models import (
    ResolutionStatus,
    EntityType,
    EntityCandidate,
    EntityResolution,
    VaspAttribution
)
from .resolver import EntityResolver
from .service import VaspAttributionService
from .providers.base import AddressIntelligenceProvider
from .providers.registry import LocalRegistryProvider

__all__ = [
    "ResolutionStatus",
    "EntityType",
    "EntityCandidate",
    "EntityResolution",
    "VaspAttribution",
    "EntityResolver",
    "VaspAttributionService",
    "AddressIntelligenceProvider",
    "LocalRegistryProvider"
]

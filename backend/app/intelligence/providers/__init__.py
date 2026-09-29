# backend/app/intelligence/providers/__init__.py
from .base import AddressIntelligenceProvider
from .registry import LocalRegistryProvider

__all__ = ["AddressIntelligenceProvider", "LocalRegistryProvider"]

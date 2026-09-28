# backend/app/blockchain/adapters/base.py
"""Compatibility adapter layer - redirects to canonical providers.base module."""
from ..providers.base import BlockchainProvider

__all__ = ["BlockchainProvider"]

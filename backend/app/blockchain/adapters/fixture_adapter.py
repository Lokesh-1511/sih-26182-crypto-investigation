# backend/app/blockchain/adapters/fixture_adapter.py
"""Compatibility adapter layer - redirects to canonical providers.fixture_provider module."""
from ..providers.fixture_provider import FixtureBlockchainProvider

__all__ = ["FixtureBlockchainProvider"]

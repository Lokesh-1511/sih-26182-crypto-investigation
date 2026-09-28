# backend/app/blockchain/adapters/live_adapter.py
"""Compatibility adapter layer - points to RpcProvider / BitqueryProvider."""
from ..providers.rpc_provider import RpcProvider as LiveBlockchainProvider

__all__ = ["LiveBlockchainProvider"]

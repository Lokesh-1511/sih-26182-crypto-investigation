# backend/app/blockchain/providers/bitquery_provider.py
"""
Bitquery Provider entry point - exposes BitqueryProvider from bitquery package.
"""
from .bitquery.provider import BitqueryProvider

__all__ = ["BitqueryProvider"]

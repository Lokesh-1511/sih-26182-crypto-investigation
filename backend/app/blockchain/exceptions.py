# backend/app/blockchain/exceptions.py
"""
Provider Exceptions for Blockchain Layer.
Standardizes domain and provider errors to isolate downstream layers from vendor specifics.
"""

class BlockchainProviderError(Exception):
    """Base exception for all blockchain provider errors."""
    def __init__(self, message: str = "Blockchain provider error", details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class UnsupportedChainError(BlockchainProviderError):
    """Raised when an operation is requested on an unsupported blockchain network."""
    pass


class InvalidAddressError(BlockchainProviderError):
    """Raised when an address fails blockchain-specific format or checksum validation."""
    pass


class TransactionNotFoundError(BlockchainProviderError):
    """Raised when a queried transaction hash cannot be located on-chain."""
    pass


class RateLimitError(BlockchainProviderError):
    """Raised when a blockchain provider rate limit is exceeded (HTTP 429)."""
    pass


class AuthenticationError(BlockchainProviderError):
    """Raised when provider credentials (API keys, JWT, HMAC) are invalid or rejected."""
    pass


class ProviderTimeoutError(BlockchainProviderError):
    """Raised when a provider request times out."""
    pass


class ProviderUnavailableError(BlockchainProviderError):
    """Raised when a provider service or RPC endpoint is unreachable/down."""
    pass


class ProviderResponseError(BlockchainProviderError):
    """Raised when a provider returns a malformed, unexpected, or error payload."""
    pass

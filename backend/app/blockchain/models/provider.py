# backend/app/blockchain/models/provider.py
from typing import List, Optional
from pydantic import BaseModel, Field
from .enums import Chain

class AddressValidation(BaseModel):
    valid: bool = Field(..., description="Whether address is structurally and cryptographically valid")
    checksum_valid: Optional[bool] = Field(None, description="Whether mixed-case or cryptographic checksum is valid")
    normalized_address: str = Field(..., description="Canonical or checksummed address representation")
    chain: Chain = Field(..., description="Target blockchain network")
    reason: Optional[str] = Field(None, description="Validation failure reason or formatting details")
    format_type: Optional[str] = Field(None, description="Address format scheme, e.g. EIP-55, BECH32_SEGWIT")

    @property
    def validation_message(self) -> str:
        """Compatibility property for legacy validation response."""
        return self.reason or ("Valid address" if self.valid else "Invalid address")


class ProviderCapabilities(BaseModel):
    chains: List[Chain] = Field(default_factory=list, description="Supported blockchain networks")
    supports_transactions: bool = Field(default=True, description="Can query full transactions")
    supports_transfers: bool = Field(default=True, description="Can query asset transfers")
    supports_token_metadata: bool = Field(default=True, description="Can query token metadata")
    supports_blocks: bool = Field(default=True, description="Can query block headers")
    supports_historical_data: bool = Field(default=True, description="Supports historical queries")
    supports_internal_transfers: bool = Field(default=False, description="Supports smart contract internal transfers")

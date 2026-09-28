# backend/app/blockchain/models/transfer.py
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from pydantic import BaseModel, Field, model_validator
from .enums import Chain, AssetType, TransferType

class NormalizedTransfer(BaseModel):
    transfer_id: str = Field(..., description="Deterministic or unique transfer identifier")
    tx_hash: str = Field(..., description="Transaction hash referencing the on-chain container")
    chain: Chain = Field(..., description="Blockchain network identifier")
    from_address: str = Field(..., description="Source address / sender")
    to_address: str = Field(..., description="Destination address / recipient")
    asset_type: AssetType = Field(default=AssetType.NATIVE, description="Classification of the transferred asset")
    asset_id: str = Field(..., description="Identifier of asset (e.g. 'ETH', 'USDT', or contract address)")
    asset_symbol: str = Field(..., description="Ticker symbol of the asset")
    token_contract: Optional[str] = Field(None, description="Smart contract address if token transfer")
    token_decimals: Optional[int] = Field(None, description="Token decimals used for normalization")
    raw_amount: str = Field(..., description="Exact raw blockchain amount string preserving precision")
    normalized_amount: Decimal = Field(..., description="Exact Decimal amount normalized by asset decimals")
    transfer_type: TransferType = Field(default=TransferType.NATIVE, description="Transfer mechanism")
    transfer_index: int = Field(default=0, ge=0, description="Sequential index of transfer within transaction")
    timestamp: Optional[datetime] = Field(None, description="Timestamp of transfer / block inclusion")
    evidence_ref: Optional[str] = Field(None, description="Pointer to supporting transaction-level raw evidence")

    @model_validator(mode="before")
    @classmethod
    def _coerce_legacy_and_defaults(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Compatibility with legacy tx_id -> tx_hash
            if "tx_hash" not in data and "tx_id" in data:
                data["tx_hash"] = data["tx_id"]
            elif "tx_hash" in data and "tx_id" not in data:
                data["tx_id"] = data["tx_hash"]

            # Generate transfer_id if missing
            if "transfer_id" not in data:
                tx_ref = data.get("tx_hash") or data.get("tx_id") or "tx"
                idx = data.get("transfer_index", 0)
                data["transfer_id"] = f"{tx_ref}_{idx}"

            # Compatibility with legacy chain default
            if "chain" not in data:
                data["chain"] = Chain.ETHEREUM

            # Asset & symbol handling
            if "asset_symbol" not in data and "asset" in data:
                data["asset_symbol"] = data["asset"]
            elif "asset_symbol" not in data and "token_symbol" in data and data["token_symbol"]:
                data["asset_symbol"] = data["token_symbol"]
            elif "asset_symbol" not in data:
                data["asset_symbol"] = "ETH"

            if "asset_id" not in data:
                data["asset_id"] = data.get("token_contract") or data["asset_symbol"]

            # Token contract and decimals
            if "token_contract" in data and data["token_contract"] and "asset_type" not in data:
                data["asset_type"] = AssetType.ERC20

            # Exact amount coercion
            if "normalized_amount" not in data:
                if "amount" in data:
                    raw_val = data["amount"]
                    data["normalized_amount"] = Decimal(str(raw_val))
                    if "raw_amount" not in data:
                        data["raw_amount"] = str(raw_val)
                elif "raw_amount" in data:
                    data["normalized_amount"] = Decimal(str(data["raw_amount"]))
                else:
                    data["normalized_amount"] = Decimal("0")
                    data["raw_amount"] = "0"
            elif "raw_amount" not in data:
                data["raw_amount"] = str(data["normalized_amount"])

        return data

    @property
    def tx_id(self) -> str:
        """Compatibility property for legacy consumers."""
        return self.tx_hash

    @property
    def asset(self) -> str:
        """Compatibility property for legacy consumers."""
        return self.asset_symbol

    @property
    def amount(self) -> float:
        """Compatibility float conversion for visualization and legacy graph consumers."""
        return float(self.normalized_amount)

    @property
    def token_symbol(self) -> Optional[str]:
        """Compatibility property for legacy token symbol access."""
        return self.asset_symbol

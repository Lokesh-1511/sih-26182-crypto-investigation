# backend/app/blockchain/models/asset.py
from typing import Optional
from pydantic import BaseModel, Field
from .enums import Chain, AssetType

class AssetMetadata(BaseModel):
    asset_id: str = Field(..., description="Unique asset identifier, e.g. 'ETH', 'BTC', or contract address")
    chain: Chain = Field(..., description="Target blockchain network")
    asset_type: AssetType = Field(default=AssetType.NATIVE, description="Asset classification")
    symbol: str = Field(..., description="Ticker symbol, e.g. 'USDT', 'BTC'")
    name: Optional[str] = Field(None, description="Descriptive asset name, e.g. 'Tether USD'")
    decimals: int = Field(default=18, ge=0, le=36, description="Token decimals")
    token_contract: Optional[str] = Field(None, description="Smart contract address if token")
    verified: bool = Field(default=True, description="Whether asset metadata is verified")

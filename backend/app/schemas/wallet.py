# backend/app/schemas/wallet.py
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class Chain(str, Enum):
    BTC = "BTC"
    ETH = "ETH"
    TRX = "TRX"
    BNB = "BNB"
    SOL = "SOL"
    POLYGON = "POLYGON"

class WalletValidationRequest(BaseModel):
    address: str = Field(..., description="Cryptocurrency wallet address string")
    chain: Chain = Field(..., description="Blockchain identifier")

class WalletValidationResult(BaseModel):
    valid: bool
    normalized_address: str
    chain: Chain
    format_type: Optional[str] = None
    validation_message: str

class WalletSummary(BaseModel):
    address: str
    chain: Chain
    role: str = "SUSPECT"
    label: Optional[str] = None
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    total_inbound: float = 0.0
    total_outbound: float = 0.0

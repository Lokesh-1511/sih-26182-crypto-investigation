# backend/app/blockchain/models/block.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from .enums import Chain

class BlockMetadata(BaseModel):
    chain: Chain = Field(..., description="Target blockchain network")
    block_number: Optional[int] = Field(None, description="Block height / sequence number")
    block_hash: Optional[str] = Field(None, description="Cryptographic block hash")
    timestamp: Optional[datetime] = Field(None, description="Block production timestamp")
    confirmation_count: Optional[int] = Field(None, description="Current confirmations on chain")

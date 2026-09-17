# backend/app/schemas/transaction.py
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from .wallet import Chain

class NormalizedTransfer(BaseModel):
    tx_id: str
    from_address: str
    to_address: str
    asset: str = "ETH"
    amount: float
    hop_distance: int = 0
    timestamp: Optional[datetime] = None
    token_contract: Optional[str] = None
    token_symbol: Optional[str] = None
    token_decimals: Optional[int] = None

class NormalizedTransaction(BaseModel):
    tx_id: str
    chain: Chain
    block_number: Optional[int] = None
    timestamp: datetime
    status: str = "SUCCESS"
    from_address: str
    to_address: str
    asset: str
    amount: float
    fee: float = 0.0
    raw_reference: Optional[str] = None
    source: str = "CONTROLLED_FIXTURE"
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    token_contract: Optional[str] = None
    token_symbol: Optional[str] = None
    token_decimals: Optional[int] = None
    transfers: List[NormalizedTransfer] = []

class TransactionIngestionBatch(BaseModel):
    case_id: str
    suspect_address: str
    chain: Chain
    total_transactions: int
    retrieval_source: str
    transactions: List[NormalizedTransaction]

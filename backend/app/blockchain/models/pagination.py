# backend/app/blockchain/models/pagination.py
from typing import List, Optional
from pydantic import BaseModel, Field
from .transaction import NormalizedTransaction
from .transfer import NormalizedTransfer

class TransactionPage(BaseModel):
    transactions: List[NormalizedTransaction] = Field(default_factory=list, description="List of normalized transactions")
    next_cursor: Optional[str] = Field(None, description="Opaque cursor token for next page")
    has_more: bool = Field(default=False, description="Whether more records exist")


class TransferPage(BaseModel):
    transfers: List[NormalizedTransfer] = Field(default_factory=list, description="List of normalized asset transfers")
    next_cursor: Optional[str] = Field(None, description="Opaque cursor token for next page")
    has_more: bool = Field(default=False, description="Whether more records exist")

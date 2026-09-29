# backend/app/blockchain/models/transaction.py
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Any
from pydantic import BaseModel, Field, model_validator
from .enums import Chain, TransactionStatus, TransactionType
from .transfer import NormalizedTransfer

class UTXOInput(BaseModel):
    tx_hash: Optional[str] = Field(None, description="Previous transaction hash referenced")
    output_index: Optional[int] = Field(None, description="Index of previous transaction output (vout)")
    address: Optional[str] = Field(None, description="Source address if resolved")
    raw_amount: Optional[str] = Field(None, description="Exact raw input satoshis/value string")
    normalized_amount: Optional[Decimal] = Field(None, description="Exact Decimal amount")
    script_sig: Optional[str] = Field(None, description="Script signature hex string")
    sequence: Optional[int] = Field(None, description="Sequence number")
    coinbase: Optional[str] = Field(None, description="Coinbase payload if mining reward")


class UTXOOutput(BaseModel):
    output_index: int = Field(..., description="Index of output (vout)")
    address: Optional[str] = Field(None, description="Recipient address / script pubkey address")
    raw_amount: str = Field(..., description="Exact raw output satoshis/value string")
    normalized_amount: Decimal = Field(..., description="Exact Decimal output amount")
    script_pubkey: Optional[str] = Field(None, description="Script public key hex")
    asset_symbol: str = Field(default="BTC", description="Asset symbol")


class ConfirmationMetadata(BaseModel):
    confirmed: bool = Field(default=True, description="Whether transaction is confirmed in a block")
    confirmation_count: Optional[int] = Field(None, description="Number of block confirmations")


class NormalizedTransaction(BaseModel):
    tx_hash: str = Field(..., description="Unique transaction hash on chain")
    chain: Chain = Field(..., description="Blockchain network identifier")
    block_number: Optional[int] = Field(None, description="Block height in which transaction was included")
    block_hash: Optional[str] = Field(None, description="Block hash")
    timestamp: datetime = Field(..., description="Transaction execution timestamp")
    status: TransactionStatus = Field(default=TransactionStatus.CONFIRMED, description="Execution status")
    transaction_type: TransactionType = Field(default=TransactionType.NATIVE_TRANSFER, description="Transaction type")
    fee: Optional[Decimal] = Field(None, description="Transaction network fee in exact Decimal")
    fee_asset: Optional[str] = Field(None, description="Asset ticker symbol used for fee payment")
    inputs: List[UTXOInput] = Field(default_factory=list, description="UTXO inputs for Bitcoin/UTXO chains")
    outputs: List[UTXOOutput] = Field(default_factory=list, description="UTXO outputs for Bitcoin/UTXO chains")
    transfers: List[NormalizedTransfer] = Field(default_factory=list, description="Canonical normalized transfers in tx")
    provider: str = Field(..., description="Blockchain provider identifier, e.g. 'FIXTURE', 'BITQUERY', 'RPC'")
    raw_reference: Optional[str] = Field(None, description="Reference URI/key for raw payload storage")
    raw_payload_hash: Optional[str] = Field(None, description="SHA-256 integrity hash of raw provider payload")
    retrieved_at: datetime = Field(default_factory=datetime.utcnow, description="Ingestion timestamp")
    confirmation: Optional[ConfirmationMetadata] = Field(
        default_factory=ConfirmationMetadata,
        description="Block confirmation state"
    )

    @model_validator(mode="before")
    @classmethod
    def _coerce_legacy_and_defaults(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Compatibility with legacy tx_id -> tx_hash
            if "tx_hash" not in data and "tx_id" in data:
                data["tx_hash"] = data["tx_id"]

            # Provider compatibility
            if "provider" not in data:
                data["provider"] = data.get("source", "FIXTURE")

            # Timestamp parsing
            if "timestamp" in data and isinstance(data["timestamp"], str):
                ts = data["timestamp"].replace("Z", "+00:00")
                data["timestamp"] = datetime.fromisoformat(ts)

            # Fee exact Decimal conversion
            if "fee" in data and data["fee"] is not None and not isinstance(data["fee"], Decimal):
                data["fee"] = Decimal(str(data["fee"]))

            # Chain default
            if "chain" not in data:
                data["chain"] = Chain.ETHEREUM

        return data

    @property
    def tx_id(self) -> str:
        """Compatibility property for legacy code."""
        return self.tx_hash

    @property
    def source(self) -> str:
        """Compatibility property for legacy code."""
        return self.provider

    @property
    def from_address(self) -> str:
        """Compatibility getter for single-sender representation."""
        if self.transfers:
            return self.transfers[0].from_address
        if self.inputs and self.inputs[0].address:
            return self.inputs[0].address
        return ""

    @property
    def to_address(self) -> str:
        """Compatibility getter for single-recipient representation."""
        if self.transfers:
            return self.transfers[0].to_address
        if self.outputs and self.outputs[0].address:
            return self.outputs[0].address
        return ""

    @property
    def asset(self) -> str:
        """Compatibility getter for primary asset."""
        if self.transfers:
            return self.transfers[0].asset_symbol
        return self.fee_asset or "ETH"

    @property
    def amount(self) -> float:
        """Compatibility getter for total transferred value in float."""
        if self.transfers:
            return sum(t.amount for t in self.transfers)
        return 0.0


class TransactionIngestionBatch(BaseModel):
    case_id: str = Field(..., description="Investigation case identifier")
    suspect_address: str = Field(..., description="Target wallet address")
    chain: Chain = Field(..., description="Blockchain network identifier")
    total_transactions: int = Field(..., description="Total transactions in batch")
    retrieval_source: str = Field(default="BLOCKCHAIN_PROVIDER", description="Provider identifier")
    transactions: List[NormalizedTransaction] = Field(default_factory=list, description="Ingested normalized transactions")
    all_transfers: List[NormalizedTransfer] = Field(default_factory=list, description="All collected normalized transfers")
    node_hop_map: dict[str, int] = Field(default_factory=dict, description="Address to hop distance mapping")
    boundary_nodes: dict[str, str] = Field(default_factory=dict, description="Boundary addresses mapped to boundary reason")
    max_hops_reached: bool = Field(default=False, description="Whether traversal reached requested max_hops boundary")
    transaction_limit_reached: bool = Field(default=False, description="Whether expansion stopped due to transaction limit")
    actual_max_hops: int = Field(default=0, description="Actual maximum hop depth reached")
    termination_reason: str = Field(default="COMPLETED", description="Ingestion termination reason")

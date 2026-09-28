# backend/app/blockchain/normalization/evm.py
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List
from .base import BaseNormalizer
from .amount import to_normalized_amount, to_raw_amount
from ..models.enums import Chain, TransactionStatus, TransactionType, AssetType, TransferType
from ..models.transaction import NormalizedTransaction, ConfirmationMetadata
from ..models.transfer import NormalizedTransfer

class EVMNormalizer(BaseNormalizer):
    """Normalizes EVM account-based transactions (Ethereum, BNB Chain, Polygon)."""

    def __init__(self, chain: Chain = Chain.ETHEREUM):
        self._chain = chain

    @property
    def supported_chain(self) -> Chain:
        return self._chain

    def _get_native_symbol(self) -> str:
        if self._chain == Chain.BNB:
            return "BNB"
        elif self._chain == Chain.POLYGON:
            return "MATIC"
        return "ETH"

    def normalize_transaction(
        self,
        raw_tx: Dict[str, Any],
        provider: str = "PROVIDER"
    ) -> NormalizedTransaction:
        tx_hash = raw_tx.get("hash") or raw_tx.get("tx_hash") or raw_tx.get("tx_id", "")
        block_number = raw_tx.get("blockNumber") or raw_tx.get("block_number")
        block_hash = raw_tx.get("blockHash") or raw_tx.get("block_hash")

        # Timestamp parsing
        ts_raw = raw_tx.get("timestamp") or raw_tx.get("block_time")
        if isinstance(ts_raw, str):
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        elif isinstance(ts_raw, (int, float)):
            ts = datetime.utcfromtimestamp(ts_raw)
        else:
            ts = datetime.utcnow()

        from_addr = raw_tx.get("from") or raw_tx.get("from_address", "")
        to_addr = raw_tx.get("to") or raw_tx.get("to_address", "")
        native_sym = self._get_native_symbol()

        # Fee computation
        fee_raw = raw_tx.get("fee")
        if fee_raw is not None:
            fee_dec = Decimal(str(fee_raw)) if isinstance(fee_raw, float) or "." in str(fee_raw) else to_normalized_amount(fee_raw, 18)
        elif "gasUsed" in raw_tx and "gasPrice" in raw_tx:
            gas_used = int(raw_tx["gasUsed"])
            gas_price = int(raw_tx["gasPrice"])
            fee_wei = gas_used * gas_price
            fee_dec = to_normalized_amount(fee_wei, 18)
        else:
            fee_dec = Decimal("0")

        # Parse transfers
        transfers: List[NormalizedTransfer] = []
        transfer_idx = 0

        # Check for token transfers (ERC-20/BEP-20 logs or explicit array)
        token_transfers_raw = raw_tx.get("token_transfers") or raw_tx.get("tokenTransfers") or []
        for tt in token_transfers_raw:
            t_from = tt.get("from") or tt.get("from_address", from_addr)
            t_to = tt.get("to") or tt.get("to_address", to_addr)
            contract = tt.get("contract_address") or tt.get("token_contract")
            sym = tt.get("symbol") or tt.get("token_symbol") or "TOKEN"
            dec = int(tt.get("decimals") or tt.get("token_decimals") or 18)
            val = tt.get("amount") or tt.get("value") or 0
            
            norm_amt = to_normalized_amount(val, dec)
            raw_amt_str = to_raw_amount(norm_amt, dec)

            transfers.append(NormalizedTransfer(
                transfer_id=f"{tx_hash}_{transfer_idx}",
                tx_hash=tx_hash,
                chain=self._chain,
                from_address=t_from,
                to_address=t_to,
                asset_type=AssetType.ERC20 if self._chain != Chain.BNB else AssetType.BEP20,
                asset_id=contract or sym,
                asset_symbol=sym,
                token_contract=contract,
                token_decimals=dec,
                raw_amount=raw_amt_str,
                normalized_amount=norm_amt,
                transfer_type=TransferType.TOKEN,
                transfer_index=transfer_idx,
                timestamp=ts,
                evidence_ref=f"tx:{tx_hash}#log:{transfer_idx}"
            ))
            transfer_idx += 1

        # Direct native value transfer (if present or if no token transfers exist)
        val_raw = raw_tx.get("value") or raw_tx.get("amount", 0)
        norm_val = to_normalized_amount(val_raw, 18)
        if norm_val > 0 or not transfers:
            transfers.insert(0, NormalizedTransfer(
                transfer_id=f"{tx_hash}_0",
                tx_hash=tx_hash,
                chain=self._chain,
                from_address=from_addr,
                to_address=to_addr,
                asset_type=AssetType.NATIVE,
                asset_id=native_sym,
                asset_symbol=native_sym,
                token_contract=None,
                token_decimals=18,
                raw_amount=to_raw_amount(norm_val, 18),
                normalized_amount=norm_val,
                transfer_type=TransferType.NATIVE,
                transfer_index=0,
                timestamp=ts,
                evidence_ref=f"tx:{tx_hash}#call"
            ))

        # Determine transaction type
        if token_transfers_raw and norm_val > 0:
            tx_type = TransactionType.MIXED
        elif token_transfers_raw:
            tx_type = TransactionType.TOKEN_TRANSFER
        elif raw_tx.get("input") and raw_tx.get("input") != "0x":
            tx_type = TransactionType.CONTRACT_CALL
        else:
            tx_type = TransactionType.NATIVE_TRANSFER

        status_str = raw_tx.get("status")
        status = TransactionStatus.CONFIRMED if status_str in (None, "SUCCESS", "confirmed", 1, "0x1") else TransactionStatus(status_str)
        payload_hash = self.calculate_payload_hash(raw_tx)

        return NormalizedTransaction(
            tx_hash=tx_hash,
            chain=self._chain,
            block_number=block_number,
            block_hash=block_hash,
            timestamp=ts,
            status=status,
            transaction_type=tx_type,
            fee=fee_dec,
            fee_asset=native_sym,
            inputs=[],
            outputs=[],
            transfers=transfers,
            provider=provider,
            raw_reference=raw_tx.get("raw_reference") or f"provider://{provider}/tx/{tx_hash}",
            raw_payload_hash=payload_hash,
            retrieved_at=datetime.utcnow(),
            confirmation=ConfirmationMetadata(
                confirmed=status == TransactionStatus.CONFIRMED,
                confirmation_count=raw_tx.get("confirmations", 1)
            )
        )

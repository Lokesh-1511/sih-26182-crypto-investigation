# backend/app/blockchain/normalization/tron.py
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List
from .base import BaseNormalizer
from .amount import to_normalized_amount, to_raw_amount
from ..models.enums import Chain, TransactionStatus, TransactionType, AssetType, TransferType
from ..models.transaction import NormalizedTransaction, ConfirmationMetadata
from ..models.transfer import NormalizedTransfer

class TronNormalizer(BaseNormalizer):
    """Normalizes TRON blockchain transactions and TRC-20 transfers."""

    @property
    def supported_chain(self) -> Chain:
        return Chain.TRON

    def normalize_transaction(
        self,
        raw_tx: Dict[str, Any],
        provider: str = "PROVIDER"
    ) -> NormalizedTransaction:
        tx_hash = raw_tx.get("txID") or raw_tx.get("hash") or raw_tx.get("tx_id", "")
        block_number = raw_tx.get("blockNumber") or raw_tx.get("block_number")
        block_hash = raw_tx.get("block_hash")

        # Timestamp parsing
        ts_raw = raw_tx.get("raw_data", {}).get("timestamp") if isinstance(raw_tx.get("raw_data"), dict) else None
        if not ts_raw:
            ts_raw = raw_tx.get("timestamp") or raw_tx.get("block_time")

        if isinstance(ts_raw, str):
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        elif isinstance(ts_raw, (int, float)):
            # Tron timestamps are in milliseconds
            ts = datetime.utcfromtimestamp(ts_raw / 1000.0 if ts_raw > 1e11 else ts_raw)
        else:
            ts = datetime.utcnow()

        from_addr = raw_tx.get("owner_address") or raw_tx.get("from_address") or raw_tx.get("from", "")
        to_addr = raw_tx.get("to_address") or raw_tx.get("to", "")

        # Fee in sun (1 TRX = 1,000,000 SUN)
        fee_raw = raw_tx.get("fee", 0)
        fee_dec = to_normalized_amount(fee_raw, 6) if isinstance(fee_raw, int) and fee_raw > 1000 else Decimal(str(fee_raw))

        transfers: List[NormalizedTransfer] = []
        transfer_idx = 0

        # TRC-20 transfers
        trc20_transfers = raw_tx.get("trc20_transfers") or raw_tx.get("token_transfers") or []
        for tt in trc20_transfers:
            t_from = tt.get("from") or tt.get("from_address", from_addr)
            t_to = tt.get("to") or tt.get("to_address", to_addr)
            contract = tt.get("contract_address") or tt.get("token_contract")
            sym = tt.get("symbol") or tt.get("token_symbol") or "USDT"
            dec = int(tt.get("decimals") or tt.get("token_decimals") or 6)
            val = tt.get("amount") or tt.get("value") or 0

            norm_amt = to_normalized_amount(val, dec)
            raw_amt_str = to_raw_amount(norm_amt, dec)

            transfers.append(NormalizedTransfer(
                transfer_id=f"{tx_hash}_{transfer_idx}",
                tx_hash=tx_hash,
                chain=Chain.TRON,
                from_address=t_from,
                to_address=t_to,
                asset_type=AssetType.TRC20,
                asset_id=contract or sym,
                asset_symbol=sym,
                token_contract=contract,
                token_decimals=dec,
                raw_amount=raw_amt_str,
                normalized_amount=norm_amt,
                transfer_type=TransferType.TOKEN,
                transfer_index=transfer_idx,
                timestamp=ts,
                evidence_ref=f"tx:{tx_hash}#trc20:{transfer_idx}"
            ))
            transfer_idx += 1

        # Direct TRX native transfer
        val_raw = raw_tx.get("amount") or raw_tx.get("value", 0)
        norm_val = to_normalized_amount(val_raw, 6)
        if norm_val > 0 or not transfers:
            transfers.insert(0, NormalizedTransfer(
                transfer_id=f"{tx_hash}_0",
                tx_hash=tx_hash,
                chain=Chain.TRON,
                from_address=from_addr,
                to_address=to_addr,
                asset_type=AssetType.NATIVE,
                asset_id="TRX",
                asset_symbol="TRX",
                token_contract=None,
                token_decimals=6,
                raw_amount=to_raw_amount(norm_val, 6),
                normalized_amount=norm_val,
                transfer_type=TransferType.NATIVE,
                transfer_index=0,
                timestamp=ts,
                evidence_ref=f"tx:{tx_hash}#trx"
            ))

        tx_type = TransactionType.TOKEN_TRANSFER if trc20_transfers else TransactionType.NATIVE_TRANSFER
        status_str = raw_tx.get("status")
        status = TransactionStatus.CONFIRMED if status_str in (None, "SUCCESS", "confirmed") else TransactionStatus(status_str)
        payload_hash = self.calculate_payload_hash(raw_tx)

        return NormalizedTransaction(
            tx_hash=tx_hash,
            chain=Chain.TRON,
            block_number=block_number,
            block_hash=block_hash,
            timestamp=ts,
            status=status,
            transaction_type=tx_type,
            fee=fee_dec,
            fee_asset="TRX",
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

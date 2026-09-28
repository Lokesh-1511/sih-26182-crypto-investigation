# backend/app/blockchain/normalization/bitcoin.py
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List
from .base import BaseNormalizer
from .amount import to_normalized_amount, to_raw_amount
from ..models.enums import Chain, TransactionStatus, TransactionType, AssetType, TransferType
from ..models.transaction import NormalizedTransaction, UTXOInput, UTXOOutput, ConfirmationMetadata
from ..models.transfer import NormalizedTransfer

class BitcoinNormalizer(BaseNormalizer):
    """Normalizes Bitcoin UTXO-based transactions and blocks."""

    @property
    def supported_chain(self) -> Chain:
        return Chain.BITCOIN

    def normalize_transaction(
        self,
        raw_tx: Dict[str, Any],
        provider: str = "PROVIDER"
    ) -> NormalizedTransaction:
        tx_hash = raw_tx.get("txid") or raw_tx.get("tx_hash") or raw_tx.get("tx_id", "")
        block_number = raw_tx.get("block_height") or raw_tx.get("block_number")
        block_hash = raw_tx.get("block_hash")

        # Timestamp parsing
        ts_raw = raw_tx.get("status", {}).get("block_time") if isinstance(raw_tx.get("status"), dict) else None
        if not ts_raw:
            ts_raw = raw_tx.get("timestamp") or raw_tx.get("block_time")
        
        if isinstance(ts_raw, str):
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        elif isinstance(ts_raw, (int, float)):
            ts = datetime.utcfromtimestamp(ts_raw)
        else:
            ts = datetime.utcnow()

        # Parse inputs
        inputs: List[UTXOInput] = []
        raw_inputs = raw_tx.get("vin") or raw_tx.get("inputs", [])
        primary_input_addr = "COINBASE"
        
        for inp in raw_inputs:
            prevout = inp.get("prevout", {}) if isinstance(inp.get("prevout"), dict) else {}
            inp_addr = prevout.get("scriptpubkey_address") or inp.get("address") or inp.get("from_address")
            if inp_addr and primary_input_addr == "COINBASE":
                primary_input_addr = inp_addr
            
            inp_val = prevout.get("value") or inp.get("value") or inp.get("amount")
            inp_dec = to_normalized_amount(inp_val, 8) if inp_val is not None else None
            inp_raw_str = to_raw_amount(inp_dec, 8) if inp_dec is not None else None

            inputs.append(UTXOInput(
                tx_hash=inp.get("txid") or inp.get("tx_hash"),
                output_index=inp.get("vout") or inp.get("output_index"),
                address=inp_addr,
                raw_amount=inp_raw_str,
                normalized_amount=inp_dec,
                script_sig=inp.get("scriptsig") or inp.get("script_sig"),
                sequence=inp.get("sequence"),
                coinbase=inp.get("coinbase")
            ))

        # If direct fixture format without vin/vout
        if not inputs and "from_address" in raw_tx:
            primary_input_addr = raw_tx["from_address"]
            inputs.append(UTXOInput(
                address=raw_tx["from_address"],
                raw_amount=to_raw_amount(raw_tx.get("amount", 0), 8),
                normalized_amount=to_normalized_amount(raw_tx.get("amount", 0), 8)
            ))

        # Parse outputs
        outputs: List[UTXOOutput] = []
        raw_outputs = raw_tx.get("vout") or raw_tx.get("outputs", [])
        transfers: List[NormalizedTransfer] = []
        
        output_idx = 0
        for out in raw_outputs:
            out_addr = out.get("scriptpubkey_address") or out.get("address") or out.get("to_address", "")
            out_val = out.get("value") or out.get("amount", 0)
            
            # Explorer APIs provide satoshis as integers
            if isinstance(out_val, int):
                out_dec = to_normalized_amount(out_val, 8)
                out_raw_str = str(out_val)
            else:
                out_dec = to_normalized_amount(out_val, 8)
                out_raw_str = to_raw_amount(out_dec, 8)

            outputs.append(UTXOOutput(
                output_index=out.get("n", output_idx),
                address=out_addr,
                raw_amount=out_raw_str,
                normalized_amount=out_dec,
                script_pubkey=out.get("scriptpubkey") or out.get("script_pubkey")
            ))

            # Generate canonical transfer for output
            transfers.append(NormalizedTransfer(
                transfer_id=f"{tx_hash}_{output_idx}",
                tx_hash=tx_hash,
                chain=Chain.BITCOIN,
                from_address=primary_input_addr,
                to_address=out_addr,
                asset_type=AssetType.NATIVE,
                asset_id="BTC",
                asset_symbol="BTC",
                token_contract=None,
                token_decimals=8,
                raw_amount=out_raw_str,
                normalized_amount=out_dec,
                transfer_type=TransferType.UTXO_OUTPUT,
                transfer_index=output_idx,
                timestamp=ts,
                evidence_ref=f"tx:{tx_hash}#out:{output_idx}"
            ))
            output_idx += 1

        # Fallback for fixture transfers
        if not outputs and "to_address" in raw_tx:
            amt_dec = to_normalized_amount(raw_tx.get("amount", 0), 8)
            amt_raw = to_raw_amount(amt_dec, 8)
            outputs.append(UTXOOutput(
                output_index=0,
                address=raw_tx["to_address"],
                raw_amount=amt_raw,
                normalized_amount=amt_dec
            ))
            transfers.append(NormalizedTransfer(
                transfer_id=f"{tx_hash}_0",
                tx_hash=tx_hash,
                chain=Chain.BITCOIN,
                from_address=primary_input_addr,
                to_address=raw_tx["to_address"],
                asset_type=AssetType.NATIVE,
                asset_id="BTC",
                asset_symbol="BTC",
                token_contract=None,
                token_decimals=8,
                raw_amount=amt_raw,
                normalized_amount=amt_dec,
                transfer_type=TransferType.UTXO_OUTPUT,
                transfer_index=0,
                timestamp=ts,
                evidence_ref=f"tx:{tx_hash}#out:0"
            ))

        # Fee calculation
        fee_raw = raw_tx.get("fee", 0)
        fee_dec = to_normalized_amount(fee_raw, 8) if isinstance(fee_raw, int) and fee_raw > 1000 else Decimal(str(fee_raw))

        status_str = raw_tx.get("status")
        status = TransactionStatus.CONFIRMED if status_str in (None, "SUCCESS", "confirmed") else TransactionStatus(status_str)

        payload_hash = self.calculate_payload_hash(raw_tx)

        return NormalizedTransaction(
            tx_hash=tx_hash,
            chain=Chain.BITCOIN,
            block_number=block_number,
            block_hash=block_hash,
            timestamp=ts,
            status=status,
            transaction_type=TransactionType.UTXO_TRANSACTION,
            fee=fee_dec,
            fee_asset="BTC",
            inputs=inputs,
            outputs=outputs,
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

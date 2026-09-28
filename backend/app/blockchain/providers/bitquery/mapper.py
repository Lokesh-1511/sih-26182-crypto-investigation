# backend/app/blockchain/providers/bitquery/mapper.py
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from typing import Dict, Any, List, Optional

from ...models.enums import (
    Chain,
    TransactionStatus,
    TransactionType,
    AssetType,
    TransferType,
)
from ...models.transaction import (
    NormalizedTransaction,
    ConfirmationMetadata,
)
from ...models.transfer import NormalizedTransfer
from ...models.block import BlockMetadata
from ...models.asset import AssetMetadata
from ...normalization.amount import to_normalized_amount, to_raw_amount

def _calculate_payload_hash(raw_record: Any) -> str:
    """Compute deterministic SHA-256 integrity hash of raw payload."""
    canonical_json = json.dumps(raw_record, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def _parse_utc_datetime(dt_raw: Any) -> datetime:
    """Safely parse Bitquery ISO-8601 timestamp as timezone-aware UTC datetime."""
    if isinstance(dt_raw, str):
        # Clean 'Z' to '+00:00'
        cleaned = dt_raw.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(cleaned)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    elif isinstance(dt_raw, (int, float)):
        return datetime.fromtimestamp(dt_raw, timezone.utc)
    
    return datetime.now(timezone.utc)


class BitqueryEVMMapper:
    """
    Transforms Bitquery V2 EVM (Ethereum) GraphQL payloads into
    canonical NormalizedTransaction and NormalizedTransfer models.
    """

    @classmethod
    def map_transfers(cls, raw_transfers: List[Dict[str, Any]]) -> List[NormalizedTransfer]:
        """
        Maps a list of raw Bitquery EVM transfer records into NormalizedTransfer objects,
        tracking occurrence counts per unique (tx_hash, loc_key) to guarantee unique, deterministic transfer IDs.
        """
        results: List[NormalizedTransfer] = []
        seen_keys: Dict[str, int] = {}
        for item in raw_transfers:
            tx_info = item.get("Transaction", {}) or {}
            tx_hash = (tx_info.get("Hash") or item.get("tx_hash", "")).lower()

            log_obj = item.get("Log") or {}
            log_idx = log_obj.get("Index") if isinstance(log_obj, dict) else None

            call_obj = item.get("Call") or {}
            call_idx = call_obj.get("Index") if isinstance(call_obj, dict) else None

            transfer_info = item.get("Transfer", {}) or {}
            t_id = transfer_info.get("Id")
            t_idx_raw = transfer_info.get("Index")
            t_type_raw = str(transfer_info.get("Type") or "").lower()

            if log_idx is not None:
                base_key = f"log_{log_idx}"
            elif call_idx is not None:
                base_key = f"call_{call_idx}"
            elif t_id and str(t_id).strip() not in ("", "None", "0"):
                base_key = str(t_id)
            elif t_idx_raw is not None:
                base_key = f"{t_type_raw or 't'}_{t_idx_raw}"
            else:
                base_key = f"{t_type_raw or 't'}_0"

            composite_key = f"{tx_hash}:{base_key}"
            count = seen_keys.get(composite_key, 0)
            seen_keys[composite_key] = count + 1

            t = cls.map_transfer(item, fallback_index=count)
            results.append(t)
        return results

    @classmethod
    def map_transfer(
        cls,
        raw_transfer_item: Dict[str, Any],
        fallback_index: int = 0
    ) -> NormalizedTransfer:
        tx_info = raw_transfer_item.get("Transaction", {}) or {}
        tx_hash = tx_info.get("Hash") or raw_transfer_item.get("tx_hash", "")
        
        transfer_info = raw_transfer_item.get("Transfer", {}) or {}
        currency_info = transfer_info.get("Currency", {}) or {}
        
        block_info = raw_transfer_item.get("Block", {}) or {}
        ts = _parse_utc_datetime(block_info.get("Time"))

        sender = transfer_info.get("Sender") or tx_info.get("From", "")
        receiver = transfer_info.get("Receiver") or tx_info.get("To", "")

        is_native = (
            currency_info.get("Native", False)
            or currency_info.get("Symbol") == "ETH"
            or not currency_info.get("SmartContract")
        )

        symbol = currency_info.get("Symbol") or ("ETH" if is_native else "TOKEN")
        contract = None if is_native else currency_info.get("SmartContract")
        decimals = int(currency_info.get("Decimals") or (18 if is_native else 18))

        # Exact Decimal Amount Handling
        amt_val = transfer_info.get("Amount")
        if amt_val is not None and str(amt_val).strip() != "":
            norm_amount = Decimal(str(amt_val))
        else:
            norm_amount = Decimal("0")
        
        raw_amount_str = to_raw_amount(norm_amount, decimals)

        # Extract indexes from Bitquery EVM record
        call_obj = raw_transfer_item.get("Call") or {}
        call_idx = call_obj.get("Index") if isinstance(call_obj, dict) else None

        log_obj = raw_transfer_item.get("Log") or {}
        log_idx = log_obj.get("Index") if isinstance(log_obj, dict) else None

        t_id = transfer_info.get("Id")
        t_idx_raw = transfer_info.get("Index")
        t_type_raw = str(transfer_info.get("Type") or "").lower()

        # Determine primary blockchain index
        if log_idx is not None:
            transfer_index = int(log_idx)
            loc_key = f"log_{log_idx}"
        elif call_idx is not None:
            transfer_index = int(call_idx)
            loc_key = f"call_{call_idx}"
        elif t_id and str(t_id).strip() not in ("", "None", "0"):
            transfer_index = int(t_idx_raw) if t_idx_raw is not None else fallback_index
            loc_key = str(t_id)
        elif t_idx_raw is not None:
            transfer_index = int(t_idx_raw)
            loc_key = f"{t_type_raw or 't'}_{transfer_index}"
        else:
            transfer_index = fallback_index
            loc_key = f"{t_type_raw or 't'}_{fallback_index}"

        # Disambiguate duplicate zero/shared indices within the same transaction
        if fallback_index > 0:
            suffix = f"{loc_key}_{fallback_index}"
        else:
            suffix = loc_key

        transfer_id = f"ethereum:{tx_hash}:{suffix}"
        asset_id = "ETH" if is_native else f"ethereum:{contract.lower()}"
        asset_type = AssetType.NATIVE if is_native else AssetType.ERC20
        
        if is_native:
            transfer_type = TransferType.INTERNAL if t_type_raw in ("call", "internal") else TransferType.NATIVE
        else:
            transfer_type = TransferType.TOKEN
            
        evidence_ref = f"bitquery://evm/eth/tx/{tx_hash}#transfer:{suffix}"

        return NormalizedTransfer(
            transfer_id=transfer_id,
            tx_hash=tx_hash,
            chain=Chain.ETHEREUM,
            from_address=sender,
            to_address=receiver,
            asset_type=asset_type,
            asset_id=asset_id,
            asset_symbol=symbol,
            token_contract=contract,
            token_decimals=decimals,
            raw_amount=raw_amount_str,
            normalized_amount=norm_amount,
            transfer_type=transfer_type,
            transfer_index=transfer_index,
            timestamp=ts,
            evidence_ref=evidence_ref
        )

    @classmethod
    def map_transaction(
        cls,
        raw_tx_item: Dict[str, Any],
        attached_transfers: Optional[List[NormalizedTransfer]] = None
    ) -> NormalizedTransaction:
        tx_info = raw_tx_item.get("Transaction", {}) or {}
        tx_hash = tx_info.get("Hash") or raw_tx_item.get("hash", "")

        block_info = raw_tx_item.get("Block", {}) or {}
        block_num = block_info.get("Number")
        block_hash = block_info.get("Hash")
        ts = _parse_utc_datetime(block_info.get("Time"))

        # Execution Status
        status_info = raw_tx_item.get("TransactionStatus", {}) or {}
        receipt_info = raw_tx_item.get("Receipt", {}) or {}
        
        is_success = True
        if "Success" in status_info and status_info["Success"] is False:
            is_success = False
        elif "Status" in receipt_info and receipt_info["Status"] == 0:
            is_success = False

        status = TransactionStatus.CONFIRMED if is_success else TransactionStatus.FAILED

        # Fee Computation in exact Decimal
        fee_info = raw_tx_item.get("Fee", {}) or {}
        cost_val = tx_info.get("Cost")
        
        if cost_val is not None:
            # Bitquery returns Cost in ETH or base units
            fee_dec = Decimal(str(cost_val)) if "." in str(cost_val) else to_normalized_amount(cost_val, 18)
        elif "GasUsed" in receipt_info and "EffectiveGasPrice" in fee_info:
            gas_used = int(receipt_info["GasUsed"] or 0)
            gas_price = int(fee_info["EffectiveGasPrice"] or 0)
            fee_dec = to_normalized_amount(gas_used * gas_price, 18)
        else:
            fee_dec = Decimal("0")

        # Native transfer construction if value transferred and not already in attached transfers
        transfers = list(attached_transfers) if attached_transfers else []
        
        val_raw = tx_info.get("Value")
        if val_raw is not None and str(val_raw) != "0" and is_success:
            norm_val = Decimal(str(val_raw)) if "." in str(val_raw) else to_normalized_amount(val_raw, 18)
            if norm_val > 0:
                has_native = any(t.asset_type == AssetType.NATIVE and t.from_address == tx_info.get("From") for t in transfers)
                if not has_native:
                    transfers.insert(0, NormalizedTransfer(
                        transfer_id=f"ethereum:{tx_hash}:0",
                        tx_hash=tx_hash,
                        chain=Chain.ETHEREUM,
                        from_address=tx_info.get("From", ""),
                        to_address=tx_info.get("To", ""),
                        asset_type=AssetType.NATIVE,
                        asset_id="ETH",
                        asset_symbol="ETH",
                        token_contract=None,
                        token_decimals=18,
                        raw_amount=to_raw_amount(norm_val, 18),
                        normalized_amount=norm_val,
                        transfer_type=TransferType.NATIVE,
                        transfer_index=0,
                        timestamp=ts,
                        evidence_ref=f"bitquery://evm/eth/tx/{tx_hash}#native"
                    ))

        # Transaction type classification
        token_count = sum(1 for t in transfers if t.asset_type == AssetType.ERC20)
        native_count = sum(1 for t in transfers if t.asset_type == AssetType.NATIVE and t.normalized_amount > 0)
        
        if token_count > 0 and native_count > 0:
            tx_type = TransactionType.MIXED
        elif token_count > 0:
            tx_type = TransactionType.TOKEN_TRANSFER
        elif native_count > 0:
            tx_type = TransactionType.NATIVE_TRANSFER
        elif receipt_info.get("ContractAddress") or (tx_info.get("To") and str(tx_info.get("Value", "0")) == "0"):
            tx_type = TransactionType.CONTRACT_CALL
        else:
            tx_type = TransactionType.UNKNOWN

        payload_hash = _calculate_payload_hash(raw_tx_item)

        return NormalizedTransaction(
            tx_hash=tx_hash,
            chain=Chain.ETHEREUM,
            block_number=int(block_num) if block_num is not None else None,
            block_hash=block_hash,
            timestamp=ts,
            status=status,
            transaction_type=tx_type,
            fee=fee_dec,
            fee_asset="ETH",
            inputs=[],
            outputs=[],
            transfers=transfers,
            provider="bitquery",
            raw_reference=f"bitquery://evm/eth/tx/{tx_hash}",
            raw_payload_hash=payload_hash,
            retrieved_at=datetime.now(timezone.utc),
            confirmation=ConfirmationMetadata(
                confirmed=is_success,
                confirmation_count=None
            )
        )

    @classmethod
    def map_block(cls, raw_block_item: Dict[str, Any]) -> BlockMetadata:
        block_info = raw_block_item.get("Block", {}) or raw_block_item
        block_num = block_info.get("Number")
        block_hash = block_info.get("Hash")
        ts = _parse_utc_datetime(block_info.get("Time"))

        return BlockMetadata(
            chain=Chain.ETHEREUM,
            block_number=int(block_num) if block_num is not None else None,
            block_hash=block_hash,
            timestamp=ts,
            confirmation_count=None
        )

    @classmethod
    def map_asset_metadata(cls, raw_transfer_item: Dict[str, Any], contract_address: str) -> Optional[AssetMetadata]:
        transfer_info = raw_transfer_item.get("Transfer", {}) or {}
        currency_info = transfer_info.get("Currency", {}) or {}

        if not currency_info:
            return None

        symbol = currency_info.get("Symbol") or "TOKEN"
        name = currency_info.get("Name") or f"{symbol} Token"
        decimals = int(currency_info.get("Decimals") or 18)
        smart_contract = currency_info.get("SmartContract") or contract_address

        return AssetMetadata(
            asset_id=f"ethereum:{smart_contract.lower()}",
            chain=Chain.ETHEREUM,
            asset_type=AssetType.ERC20,
            symbol=symbol,
            name=name,
            decimals=decimals,
            token_contract=smart_contract,
            verified=True
        )

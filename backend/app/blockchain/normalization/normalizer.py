# backend/app/blockchain/normalization/normalizer.py
from typing import Dict, Any, List
from datetime import datetime
from ...schemas.wallet import Chain
from ...schemas.transaction import NormalizedTransaction, NormalizedTransfer

class TransactionNormalizer:
    """
    Normalizes multi-chain blockchain records (UTXO, EVM Account, TRC20)
    into standard NormalizedTransaction and NormalizedTransfer structures.
    """

    @classmethod
    def normalize_account_transfer(
        cls,
        tx_data: Dict[str, Any],
        chain: Chain = Chain.ETH
    ) -> NormalizedTransaction:
        """Normalize an EVM or Tron account-based transaction."""
        tx_id = tx_data.get("hash") or tx_data.get("tx_id") or tx_data.get("transaction_id", "")
        from_addr = tx_data.get("from") or tx_data.get("from_address", "")
        to_addr = tx_data.get("to") or tx_data.get("to_address", "")
        amount = float(tx_data.get("value") or tx_data.get("amount", 0.0))
        asset = tx_data.get("asset", chain.value)
        fee = float(tx_data.get("fee", 0.0))
        block_number = tx_data.get("blockNumber") or tx_data.get("block_number")

        ts_raw = tx_data.get("timestamp")
        if isinstance(ts_raw, str):
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        elif isinstance(ts_raw, (int, float)):
            ts = datetime.utcfromtimestamp(ts_raw)
        else:
            ts = datetime.utcnow()

        # Build direct native transfer
        transfer = NormalizedTransfer(
            tx_id=tx_id,
            from_address=from_addr,
            to_address=to_addr,
            asset=asset,
            amount=amount,
            hop_distance=0,
            timestamp=ts
        )

        # Handle token transfers if present in raw payload
        token_transfers = []
        if "token_transfers" in tx_data:
            for tt in tx_data["token_transfers"]:
                token_transfers.append(NormalizedTransfer(
                    tx_id=tx_id,
                    from_address=tt.get("from", from_addr),
                    to_address=tt.get("to", to_addr),
                    asset=tt.get("symbol", "TOKEN"),
                    amount=float(tt.get("amount", 0.0)),
                    hop_distance=0,
                    timestamp=ts,
                    token_contract=tt.get("contract_address"),
                    token_symbol=tt.get("symbol"),
                    token_decimals=tt.get("decimals")
                ))

        all_transfers = token_transfers if token_transfers else [transfer]

        return NormalizedTransaction(
            tx_id=tx_id,
            chain=chain,
            block_number=block_number,
            timestamp=ts,
            status=tx_data.get("status", "SUCCESS"),
            from_address=from_addr,
            to_address=to_addr,
            asset=asset,
            amount=amount,
            fee=fee,
            raw_reference=str(tx_data),
            source=tx_data.get("source", "NORMALIZED_ACCOUNT"),
            retrieved_at=datetime.utcnow(),
            transfers=all_transfers
        )

    @classmethod
    def normalize_utxo_transaction(
        cls,
        tx_data: Dict[str, Any],
        chain: Chain = Chain.BTC
    ) -> NormalizedTransaction:
        """Normalize a Bitcoin UTXO transaction with inputs and outputs."""
        tx_id = tx_data.get("txid") or tx_data.get("tx_id", "")
        fee = float(tx_data.get("fee", 0.0))
        block_number = tx_data.get("block_height") or tx_data.get("block_number")
        
        ts_raw = tx_data.get("status", {}).get("block_time") or tx_data.get("timestamp")
        if isinstance(ts_raw, str):
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        elif isinstance(ts_raw, (int, float)):
            ts = datetime.utcfromtimestamp(ts_raw)
        else:
            ts = datetime.utcnow()

        inputs = tx_data.get("vin", [])
        outputs = tx_data.get("vout", [])

        from_addr = inputs[0].get("prevout", {}).get("scriptpubkey_address", "UTXO_INPUT") if inputs else "COINBASE"
        
        transfers = []
        total_amount = 0.0
        primary_to = ""

        for vout in outputs:
            to_addr = vout.get("scriptpubkey_address") or vout.get("address", "")
            amt = float(vout.get("value", 0.0))
            if "scriptpubkey_address" in vout:
                # Value in satoshis for Bitcoin Explorer APIs
                amt = amt / 1e8
            total_amount += amt
            if not primary_to:
                primary_to = to_addr
            
            transfers.append(NormalizedTransfer(
                tx_id=tx_id,
                from_address=from_addr,
                to_address=to_addr,
                asset="BTC",
                amount=amt,
                hop_distance=0,
                timestamp=ts
            ))

        return NormalizedTransaction(
            tx_id=tx_id,
            chain=chain,
            block_number=block_number,
            timestamp=ts,
            status="SUCCESS",
            from_address=from_addr,
            to_address=primary_to,
            asset="BTC",
            amount=total_amount,
            fee=fee / 1e8 if fee > 1000 else fee,
            raw_reference=str(tx_data),
            source="NORMALIZED_UTXO",
            retrieved_at=datetime.utcnow(),
            transfers=transfers
        )

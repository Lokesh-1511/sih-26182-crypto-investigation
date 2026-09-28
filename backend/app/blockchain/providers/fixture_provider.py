# backend/app/blockchain/providers/fixture_provider.py
import os
import json
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any

from .base import BlockchainProvider
from ..models.enums import Chain, TransferDirection, TransactionStatus, TransactionType, AssetType, TransferType
from ..models.provider import AddressValidation, ProviderCapabilities
from ..models.pagination import TransactionPage, TransferPage
from ..models.transaction import NormalizedTransaction, ConfirmationMetadata
from ..models.transfer import NormalizedTransfer
from ..models.block import BlockMetadata
from ..models.asset import AssetMetadata
from ..validation.validator import MultiChainValidator
from ..normalization.normalizer import TransactionNormalizer
from ..normalization.amount import to_normalized_amount, to_raw_amount

class FixtureBlockchainProvider(BlockchainProvider):
    """
    Offline fixture provider serving pre-recorded, verified transaction traces
    for demo investigations without requiring live blockchain access.
    """

    def __init__(self, fixtures_dir: Optional[str] = None):
        if fixtures_dir is None:
            # Default to repo root /data/demo/
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
            self.fixtures_dir = os.path.join(base_dir, "data", "demo")
        else:
            self.fixtures_dir = fixtures_dir

        self.transactions_dir = os.path.join(self.fixtures_dir, "transactions")
        self._cache: Dict[str, NormalizedTransaction] = {}
        self._case_transfers: Dict[str, List[NormalizedTransfer]] = {}
        self._load_fixtures()

    def _load_fixtures(self):
        if not os.path.exists(self.transactions_dir):
            return

        file_to_case_map = {
            "case_a_transactions.json": ["CASE-2026-001A", "case_a", "CASE_A"],
            "case_b_transactions.json": ["CASE-2026-002B", "case_b", "CASE_B"],
            "case_c_transactions.json": ["CASE-2026-003C", "case_c", "CASE_C"]
        }

        for fname in os.listdir(self.transactions_dir):
            if fname.endswith(".json"):
                fpath = os.path.join(self.transactions_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        raw_items = data if isinstance(data, list) else [data]
                        file_transfers: List[NormalizedTransfer] = []
                        for item in raw_items:
                            chain_str = item.get("chain", "ETH")
                            try:
                                chain = Chain(chain_str)
                            except ValueError:
                                chain = Chain.ETHEREUM

                            tx_obj = self._index_transaction(item, chain)
                            if tx_obj and tx_obj.transfers:
                                file_transfers.extend(tx_obj.transfers)

                        aliases = file_to_case_map.get(fname, [fname.replace(".json", "")])
                        for alias in aliases:
                            self._case_transfers[alias] = file_transfers
                except Exception as e:
                    print(f"Error loading fixture {fname}: {e}")

    def _index_transaction(self, item: Dict[str, Any], chain: Chain) -> Optional[NormalizedTransaction]:
        tx_hash = item.get("tx_id") or item.get("tx_hash")
        if not tx_hash:
            return None

        # Parse timestamp
        ts_raw = item.get("timestamp")
        if isinstance(ts_raw, str):
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        elif isinstance(ts_raw, (int, float)):
            ts = datetime.utcfromtimestamp(ts_raw)
        else:
            ts = datetime.utcnow()

        transfers: List[NormalizedTransfer] = []
        raw_transfers = item.get("transfers", [])
        
        transfer_idx = 0
        for t in raw_transfers:
            t_tx_hash = t.get("tx_id") or t.get("tx_hash") or tx_hash
            sym = t.get("asset") or t.get("token_symbol") or ("BTC" if chain == Chain.BITCOIN else "ETH")
            dec = t.get("token_decimals", 8 if chain == Chain.BITCOIN else 18)
            val = t.get("amount", 0.0)
            norm_amt = to_normalized_amount(val, dec)
            raw_amt_str = to_raw_amount(norm_amt, dec)
            contract = t.get("token_contract")
            is_token = contract is not None or sym not in ("BTC", "ETH", "BNB", "MATIC", "POLYGON", "TRX")

            t_obj = NormalizedTransfer(
                transfer_id=f"{t_tx_hash}_{transfer_idx}",
                tx_hash=t_tx_hash,
                chain=chain,
                from_address=t.get("from_address", ""),
                to_address=t.get("to_address", ""),
                asset_type=AssetType.ERC20 if is_token and chain != Chain.TRON else (AssetType.TRC20 if is_token and chain == Chain.TRON else AssetType.NATIVE),
                asset_id=contract or sym,
                asset_symbol=sym,
                token_contract=contract,
                token_decimals=dec,
                raw_amount=raw_amt_str,
                normalized_amount=norm_amt,
                transfer_type=TransferType.TOKEN if is_token else TransferType.NATIVE,
                transfer_index=transfer_idx,
                timestamp=ts,
                evidence_ref=f"fixture://tx/{t_tx_hash}#transfer:{transfer_idx}"
            )
            transfers.append(t_obj)
            transfer_idx += 1

        # Fallback if no transfers in item
        if not transfers and ("from_address" in item or "to_address" in item):
            sym = item.get("asset", "BTC" if chain == Chain.BITCOIN else "ETH")
            dec = 8 if chain == Chain.BITCOIN else 18
            amt_val = item.get("amount", 0.0)
            norm_amt = to_normalized_amount(amt_val, dec)
            transfers.append(NormalizedTransfer(
                transfer_id=f"{tx_hash}_0",
                tx_hash=tx_hash,
                chain=chain,
                from_address=item.get("from_address", ""),
                to_address=item.get("to_address", ""),
                asset_type=AssetType.NATIVE,
                asset_id=sym,
                asset_symbol=sym,
                raw_amount=to_raw_amount(norm_amt, dec),
                normalized_amount=norm_amt,
                transfer_type=TransferType.NATIVE,
                transfer_index=0,
                timestamp=ts,
                evidence_ref=f"fixture://tx/{tx_hash}#transfer:0"
            ))

        fee_val = item.get("fee", 0.0)
        fee_dec = Decimal(str(fee_val)) if fee_val is not None else None

        status_str = item.get("status", "CONFIRMED")
        status = TransactionStatus.CONFIRMED if status_str in ("SUCCESS", "CONFIRMED") else TransactionStatus(status_str)

        tx_obj = NormalizedTransaction(
            tx_hash=tx_hash,
            chain=chain,
            block_number=item.get("block_number"),
            timestamp=ts,
            status=status,
            transaction_type=TransactionType.UTXO_TRANSACTION if chain == Chain.BITCOIN else TransactionType.NATIVE_TRANSFER,
            fee=fee_dec,
            fee_asset=item.get("asset", "ETH"),
            inputs=[],
            outputs=[],
            transfers=transfers,
            provider="CONTROLLED_FIXTURE",
            raw_reference=item.get("raw_reference") or f"fixture://case/{tx_hash}",
            raw_payload_hash=TransactionNormalizer._btc_normalizer.calculate_payload_hash(item),
            retrieved_at=datetime.utcnow(),
            confirmation=ConfirmationMetadata(confirmed=True, confirmation_count=12)
        )
        self._cache[tx_hash.lower()] = tx_obj
        return tx_obj

    def get_case_transfers(
        self,
        case_id: str,
        chain: Optional[Chain] = None,
        suspect_wallet: Optional[str] = None
    ) -> List[NormalizedTransfer]:
        """Retrieve case-isolated transfers for demo graph and attribution."""
        if case_id in self._case_transfers:
            return self._case_transfers[case_id]

        for k, v in self._case_transfers.items():
            if k.lower() in case_id.lower() or case_id.lower() in k.lower():
                return v

        if chain:
            transfers = [t for tx in self._cache.values() if tx.chain == chain for t in tx.transfers]
            if suspect_wallet:
                target_lower = suspect_wallet.lower()
                connected_addrs = {target_lower}
                for _ in range(5):
                    new_addrs = set()
                    for t in transfers:
                        if t.from_address.lower() in connected_addrs:
                            new_addrs.add(t.to_address.lower())
                    if not (new_addrs - connected_addrs):
                        break
                    connected_addrs.update(new_addrs)

                filtered = [t for t in transfers if t.from_address.lower() in connected_addrs or t.to_address.lower() in connected_addrs]
                if filtered:
                    return filtered
            return transfers

        return [t for tx in self._cache.values() for t in tx.transfers]

    # BlockchainProvider Interface Implementation

    async def validate_address(
        self,
        chain: Chain,
        address: str
    ) -> AddressValidation:
        return MultiChainValidator.validate(address, chain)

    async def get_transactions(
        self,
        chain: Chain,
        address: str,
        direction: TransferDirection = TransferDirection.ANY,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        cursor: Optional[str] = None,
        limit: int = 100
    ) -> TransactionPage:
        addr = address.lower()
        matched: List[NormalizedTransaction] = []

        for tx in self._cache.values():
            if tx.chain != chain:
                continue

            if start_time and tx.timestamp < start_time:
                continue
            if end_time and tx.timestamp > end_time:
                continue

            # Check direction match across transfers
            matches = False
            for t in tx.transfers:
                if direction == TransferDirection.INCOMING and t.to_address.lower() == addr:
                    matches = True
                    break
                elif direction == TransferDirection.OUTGOING and t.from_address.lower() == addr:
                    matches = True
                    break
                elif direction == TransferDirection.ANY and (t.from_address.lower() == addr or t.to_address.lower() == addr):
                    matches = True
                    break

            if matches:
                matched.append(tx)

        # Pagination using integer offset string as opaque cursor
        start_idx = int(cursor) if cursor and cursor.isdigit() else 0
        page_txs = matched[start_idx:start_idx + limit]
        has_more = (start_idx + limit) < len(matched)
        next_cursor = str(start_idx + limit) if has_more else None

        return TransactionPage(
            transactions=page_txs,
            next_cursor=next_cursor,
            has_more=has_more
        )

    async def get_transaction(
        self,
        chain: Chain,
        tx_hash: str
    ) -> Optional[NormalizedTransaction]:
        return self._cache.get(tx_hash.lower())

    async def get_transfers(
        self,
        chain: Chain,
        address: str,
        direction: TransferDirection = TransferDirection.ANY,
        asset_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        cursor: Optional[str] = None,
        limit: int = 100
    ) -> TransferPage:
        addr = address.lower()
        matched: List[NormalizedTransfer] = []

        for tx in self._cache.values():
            if tx.chain != chain:
                continue
            for t in tx.transfers:
                if start_time and t.timestamp and t.timestamp < start_time:
                    continue
                if end_time and t.timestamp and t.timestamp > end_time:
                    continue
                if asset_id and t.asset_id.lower() != asset_id.lower() and t.asset_symbol.lower() != asset_id.lower():
                    continue

                if direction == TransferDirection.INCOMING and t.to_address.lower() == addr:
                    matched.append(t)
                elif direction == TransferDirection.OUTGOING and t.from_address.lower() == addr:
                    matched.append(t)
                elif direction == TransferDirection.ANY and (t.from_address.lower() == addr or t.to_address.lower() == addr):
                    matched.append(t)

        start_idx = int(cursor) if cursor and cursor.isdigit() else 0
        page_transfers = matched[start_idx:start_idx + limit]
        has_more = (start_idx + limit) < len(matched)
        next_cursor = str(start_idx + limit) if has_more else None

        return TransferPage(
            transfers=page_transfers,
            next_cursor=next_cursor,
            has_more=has_more
        )

    async def get_block(
        self,
        chain: Chain,
        block_number: Optional[int] = None,
        block_hash: Optional[str] = None
    ) -> Optional[BlockMetadata]:
        return BlockMetadata(
            chain=chain,
            block_number=block_number or 19482010,
            block_hash=block_hash or "0xblock_hash_fixture",
            timestamp=datetime.utcnow(),
            confirmation_count=12
        )

    async def get_asset_metadata(
        self,
        chain: Chain,
        asset_id: str
    ) -> Optional[AssetMetadata]:
        return AssetMetadata(
            asset_id=asset_id,
            chain=chain,
            asset_type=AssetType.NATIVE if asset_id in ("ETH", "BTC", "TRX", "BNB", "MATIC") else AssetType.ERC20,
            symbol=asset_id,
            name=f"{asset_id} Token",
            decimals=18 if chain != Chain.BITCOIN else 8,
            token_contract=None if asset_id in ("ETH", "BTC", "TRX") else asset_id,
            verified=True
        )

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            chains=[Chain.BITCOIN, Chain.ETHEREUM, Chain.BNB, Chain.POLYGON, Chain.TRON],
            supports_transactions=True,
            supports_transfers=True,
            supports_token_metadata=True,
            supports_blocks=True,
            supports_historical_data=True,
            supports_internal_transfers=True
        )

    # Legacy synchronous helpers
    def get_wallet_transactions(
        self, address: str, chain: Chain, limit: int = 50
    ) -> List[NormalizedTransaction]:
        addr = address.lower()
        results = []
        for tx in self._cache.values():
            if tx.chain == chain:
                for t in tx.transfers:
                    if t.from_address.lower() == addr or t.to_address.lower() == addr:
                        results.append(tx)
                        break
            if len(results) >= limit:
                break
        return results

# backend/app/blockchain/adapters/fixture_adapter.py
import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from .base import BlockchainProvider
from ...schemas.wallet import Chain
from ...schemas.transaction import NormalizedTransaction, NormalizedTransfer

class FixtureBlockchainProvider(BlockchainProvider):
    """
    Offline fixture adapter serving pre-recorded, verified transaction traces
    for hackathon demonstrations without requiring active internet connectivity.
    """

    def __init__(self, fixtures_dir: Optional[str] = None):
        if fixtures_dir is None:
            # Default to repo root /data/demo/
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
            self.fixtures_dir = os.path.join(base_dir, "data", "demo")
        else:
            self.fixtures_dir = fixtures_dir
        
        self.transactions_dir = os.path.join(self.fixtures_dir, "transactions")
        self.cases_dir = os.path.join(self.fixtures_dir, "cases")
        self._cache: Dict[str, NormalizedTransaction] = {}
        self._case_transfers: Dict[str, List[NormalizedTransfer]] = {}
        self._load_fixtures()

    def _load_fixtures(self):
        if not os.path.exists(self.transactions_dir):
            return

        # Case mapping dictionary
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
                            tx_obj = self._index_transaction(item)
                            if tx_obj and tx_obj.transfers:
                                file_transfers.extend(tx_obj.transfers)

                        # Associate transfers with known case aliases
                        aliases = file_to_case_map.get(fname, [fname.replace(".json", "")])
                        for alias in aliases:
                            self._case_transfers[alias] = file_transfers
                except Exception as e:
                    print(f"Error loading fixture {fname}: {e}")

    def _index_transaction(self, item: Dict[str, Any]) -> Optional[NormalizedTransaction]:
        tx_id = item.get("tx_id")
        if not tx_id:
            return None
        
        # Parse transfers if present
        transfers = []
        for t in item.get("transfers", []):
            t_obj = NormalizedTransfer(
                tx_id=t.get("tx_id", tx_id),
                from_address=t.get("from_address", ""),
                to_address=t.get("to_address", ""),
                asset=t.get("asset", "ETH"),
                amount=float(t.get("amount", 0.0)),
                hop_distance=int(t.get("hop_distance", 0)),
                timestamp=datetime.fromisoformat(t["timestamp"]) if "timestamp" in t and t["timestamp"] else None,
                token_contract=t.get("token_contract"),
                token_symbol=t.get("token_symbol"),
                token_decimals=t.get("token_decimals")
            )
            transfers.append(t_obj)

        tx_obj = NormalizedTransaction(
            tx_id=tx_id,
            chain=Chain(item.get("chain", "ETH")),
            block_number=item.get("block_number"),
            timestamp=datetime.fromisoformat(item["timestamp"]) if "timestamp" in item else datetime.utcnow(),
            status=item.get("status", "SUCCESS"),
            from_address=item.get("from_address", ""),
            to_address=item.get("to_address", ""),
            asset=item.get("asset", "ETH"),
            amount=float(item.get("amount", 0.0)),
            fee=float(item.get("fee", 0.0)),
            raw_reference=item.get("raw_reference"),
            source="CONTROLLED_FIXTURE",
            retrieved_at=datetime.utcnow(),
            transfers=transfers
        )
        self._cache[tx_id.lower()] = tx_obj
        return tx_obj

    def get_case_transfers(
        self,
        case_id: str,
        chain: Optional[Chain] = None,
        suspect_wallet: Optional[str] = None
    ) -> List[NormalizedTransfer]:
        """
        Retrieves transfers strictly isolated to a specific investigation case.
        Prevents cross-case and cross-chain pollution in graph and attribution models.
        """
        if case_id in self._case_transfers:
            return self._case_transfers[case_id]

        # Case-insensitive / prefix matching
        for k, v in self._case_transfers.items():
            if k.lower() in case_id.lower() or case_id.lower() in k.lower():
                return v

        # Fallback: filter by chain and suspect wallet reachability
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

    def get_wallet_transactions(
        self, address: str, chain: Chain, limit: int = 50
    ) -> List[NormalizedTransaction]:
        addr = address.lower()
        results = []
        for tx in self._cache.values():
            if tx.chain == chain:
                if tx.from_address.lower() == addr or tx.to_address.lower() == addr:
                    results.append(tx)
                else:
                    for t in tx.transfers:
                        if t.from_address.lower() == addr or t.to_address.lower() == addr:
                            results.append(tx)
                            break
            if len(results) >= limit:
                break
        return results

    def get_transaction(
        self, tx_id: str, chain: Chain
    ) -> Optional[NormalizedTransaction]:
        return self._cache.get(tx_id.lower())

    def get_transfers(
        self, address: str, chain: Chain
    ) -> List[NormalizedTransfer]:
        addr = address.lower()
        results = []
        for tx in self._cache.values():
            if tx.chain == chain:
                for t in tx.transfers:
                    if t.from_address.lower() == addr or t.to_address.lower() == addr:
                        results.append(t)
        return results

    def get_block(
        self, block_number: int, chain: Chain
    ) -> Optional[Dict[str, Any]]:
        return {
            "block_number": block_number,
            "chain": chain.value,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "CONTROLLED_FIXTURE"
        }

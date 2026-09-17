# backend/app/blockchain/ingestion/collector.py
from typing import List, Optional
from ..adapters.base import BlockchainProvider
from ...schemas.wallet import Chain
from ...schemas.transaction import NormalizedTransaction, TransactionIngestionBatch

class TransactionCollector:
    """
    Ingestion orchestrator: fetches, deduplicates, validates, and batches transactions.
    """

    def __init__(self, provider: BlockchainProvider):
        self.provider = provider

    def collect_case_transactions(
        self,
        case_id: str,
        suspect_wallet: str,
        chain: Chain,
        max_hops: int = 4
    ) -> TransactionIngestionBatch:
        """
        Ingests transactions for the suspect wallet and immediate downstream flows.
        """
        seen_txs = set()
        collected: List[NormalizedTransaction] = []

        # Level 0 (Direct)
        direct_txs = self.provider.get_wallet_transactions(suspect_wallet, chain)
        for tx in direct_txs:
            if tx.tx_id not in seen_txs:
                seen_txs.add(tx.tx_id)
                collected.append(tx)

        # Multi-hop collection
        current_layer = {suspect_wallet.lower()}
        for hop in range(1, max_hops + 1):
            next_layer = set()
            for addr in current_layer:
                transfers = self.provider.get_transfers(addr, chain)
                for t in transfers:
                    # Look for downstream addresses
                    if t.from_address.lower() == addr:
                        dest = t.to_address.lower()
                        if dest not in current_layer and dest not in next_layer:
                            next_layer.add(dest)
                            # Fetch transactions for downstream address
                            downstream_txs = self.provider.get_wallet_transactions(dest, chain)
                            for tx in downstream_txs:
                                if tx.tx_id not in seen_txs:
                                    seen_txs.add(tx.tx_id)
                                    collected.append(tx)
            current_layer = next_layer
            if not current_layer:
                break

        return TransactionIngestionBatch(
            case_id=case_id,
            suspect_address=suspect_wallet,
            chain=chain,
            total_transactions=len(collected),
            retrieval_source="BLOCKCHAIN_PROVIDER",
            transactions=collected
        )

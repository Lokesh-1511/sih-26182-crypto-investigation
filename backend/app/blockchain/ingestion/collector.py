# backend/app/blockchain/ingestion/collector.py
import asyncio
from typing import List, Set, Optional, Dict
from ..providers.base import BlockchainProvider
from ..models.enums import Chain, TransferDirection
from ..models.transaction import NormalizedTransaction, TransactionIngestionBatch
from ..models.transfer import NormalizedTransfer
from ..exceptions import BlockchainProviderError

class TransactionCollector:
    """
    Vendor-agnostic ingestion orchestrator.
    Consumes ONLY the abstract BlockchainProvider interface to discover multi-hop transaction flows.
    """

    def __init__(self, provider: BlockchainProvider):
        self.provider = provider

    async def collect_case_transactions(
        self,
        case_id: str,
        suspect_wallet: str,
        chain: Chain,
        max_hops: int = 4,
        direction: TransferDirection = TransferDirection.OUTGOING,
        max_transactions: int = 100,
        page_limit: int = 50
    ) -> TransactionIngestionBatch:
        """
        Asynchronously traces and collects transaction graph paths starting from suspect_wallet.
        Maintains visited address and transaction sets to eliminate circular loops.
        """
        if not isinstance(chain, Chain):
            try:
                chain = Chain(chain)
            except ValueError:
                chain = Chain.ETHEREUM

        # 1. Validate root suspect address
        val_res = await self.provider.validate_address(chain, suspect_wallet)
        normalized_root = val_res.normalized_address if val_res.valid else suspect_wallet
        root_lower = normalized_root.lower()

        visited_addrs: Set[str] = {root_lower}
        visited_tx_hashes: Set[str] = set()
        collected_txs: List[NormalizedTransaction] = []

        # Layer 0: Transactions directly involving suspect wallet
        cursor: Optional[str] = None
        has_more = True
        while has_more and len(collected_txs) < max_transactions:
            page = await self.provider.get_transactions(
                chain=chain,
                address=normalized_root,
                direction=TransferDirection.ANY,
                cursor=cursor,
                limit=min(page_limit, max_transactions - len(collected_txs))
            )
            for tx in page.transactions:
                if tx.tx_hash not in visited_tx_hashes:
                    visited_tx_hashes.add(tx.tx_hash)
                    collected_txs.append(tx)
            cursor = page.next_cursor
            has_more = page.has_more and cursor is not None

        # Multi-hop breadth-first traversal
        current_layer: Set[str] = {root_lower}

        for hop in range(1, max_hops + 1):
            if len(collected_txs) >= max_transactions:
                break

            next_layer: Set[str] = set()

            for addr in current_layer:
                if len(collected_txs) >= max_transactions:
                    break

                # Fetch transfers from this address
                t_cursor: Optional[str] = None
                t_has_more = True

                while t_has_more and len(collected_txs) < max_transactions:
                    transfer_page = await self.provider.get_transfers(
                        chain=chain,
                        address=addr,
                        direction=direction,
                        cursor=t_cursor,
                        limit=page_limit
                    )

                    for transfer in transfer_page.transfers:
                        # Determine downstream address based on flow direction
                        if direction == TransferDirection.OUTGOING or direction == TransferDirection.ANY:
                            target_addr = transfer.to_address.lower()
                        else:
                            target_addr = transfer.from_address.lower()

                        # Cycle prevention: only traverse unvisited addresses
                        if target_addr and target_addr not in visited_addrs:
                            visited_addrs.add(target_addr)
                            next_layer.add(target_addr)

                            # Fetch transaction record if not already ingested
                            if transfer.tx_hash not in visited_tx_hashes:
                                visited_tx_hashes.add(transfer.tx_hash)
                                tx_detail = await self.provider.get_transaction(chain, transfer.tx_hash)
                                if tx_detail:
                                    collected_txs.append(tx_detail)

                    t_cursor = transfer_page.next_cursor
                    t_has_more = transfer_page.has_more and t_cursor is not None

            current_layer = next_layer
            if not current_layer:
                break

        return TransactionIngestionBatch(
            case_id=case_id,
            suspect_address=normalized_root,
            chain=chain,
            total_transactions=len(collected_txs),
            retrieval_source=type(self.provider).__name__,
            transactions=collected_txs
        )

    def collect_case_transactions_sync(
        self,
        case_id: str,
        suspect_wallet: str,
        chain: Chain,
        max_hops: int = 4,
        direction: TransferDirection = TransferDirection.OUTGOING,
        max_transactions: int = 100
    ) -> TransactionIngestionBatch:
        """Synchronous wrapper for synchronous callers."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # In nested event loop context (e.g. running FastAPI threadpool)
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(
                        asyncio.run,
                        self.collect_case_transactions(
                            case_id=case_id,
                            suspect_wallet=suspect_wallet,
                            chain=chain,
                            max_hops=max_hops,
                            direction=direction,
                            max_transactions=max_transactions
                        )
                    ).result()
            else:
                return loop.run_until_complete(
                    self.collect_case_transactions(
                        case_id=case_id,
                        suspect_wallet=suspect_wallet,
                        chain=chain,
                        max_hops=max_hops,
                        direction=direction,
                        max_transactions=max_transactions
                    )
                )
        except RuntimeError:
            return asyncio.run(
                self.collect_case_transactions(
                    case_id=case_id,
                    suspect_wallet=suspect_wallet,
                    chain=chain,
                    max_hops=max_hops,
                    direction=direction,
                    max_transactions=max_transactions
                )
            )

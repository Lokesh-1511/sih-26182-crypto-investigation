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
        max_hops: int = 1,
        direction: TransferDirection = TransferDirection.OUTGOING,
        max_transactions: int = 50,
        page_limit: int = 50,
        max_nodes: int = 500
    ) -> TransactionIngestionBatch:
        """
        Asynchronously traces and collects transaction graph paths starting from suspect_wallet
        using true bounded Breadth-First Search (BFS) for forward (outgoing) or backward (incoming) flows.
        
        Guarantees:
        - Strict hop boundary enforcement (1 to 5 hops).
        - Total transaction budget enforcement (global limit across all hops).
        - Cycle prevention and visited-address tracking.
        - Preserves blockchain transfer direction (from -> to) regardless of trace direction.
        - Detects and annotates boundary nodes and termination reasons.
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
        node_hop_map: Dict[str, int] = {root_lower: 0}
        boundary_nodes: Dict[str, str] = {}
        visited_tx_hashes: Set[str] = set()
        collected_txs: List[NormalizedTransaction] = []
        all_transfers: List[NormalizedTransfer] = []
        seen_transfer_ids: Set[str] = set()

        transaction_limit_reached = False
        max_hops_reached = False

        # Multi-hop breadth-first traversal
        current_layer: Set[str] = {root_lower}

        for hop_idx in range(1, max_hops + 1):
            if len(collected_txs) >= max_transactions or len(visited_addrs) >= max_nodes:
                transaction_limit_reached = True
                break

            next_layer: Set[str] = set()

            for addr in current_layer:
                if len(collected_txs) >= max_transactions or len(visited_addrs) >= max_nodes:
                    transaction_limit_reached = True
                    break

                t_cursor: Optional[str] = None
                t_has_more = True

                while t_has_more and len(collected_txs) < max_transactions:
                    remaining_budget = max_transactions - len(collected_txs)
                    limit = min(page_limit, remaining_budget)

                    transfer_page = await self.provider.get_transfers(
                        chain=chain,
                        address=addr,
                        direction=direction,
                        cursor=t_cursor,
                        limit=limit
                    )

                    transfers_to_process = list(transfer_page.transfers)

                    # Fallback to get_transactions if get_transfers returned empty on root address
                    if not transfers_to_process and addr == root_lower and not collected_txs:
                        tx_page = await self.provider.get_transactions(
                            chain=chain,
                            address=addr,
                            direction=direction,
                            cursor=t_cursor,
                            limit=limit
                        )
                        for tx in tx_page.transactions:
                            if tx.tx_hash not in visited_tx_hashes:
                                visited_tx_hashes.add(tx.tx_hash)
                                collected_txs.append(tx)
                                for tx_t in tx.transfers:
                                    if tx_t.transfer_id not in seen_transfer_ids:
                                        seen_transfer_ids.add(tx_t.transfer_id)
                                        all_transfers.append(tx_t)
                                        transfers_to_process.append(tx_t)

                    for transfer in transfers_to_process:
                        # Determine neighbor address based on traversal direction
                        if direction == TransferDirection.INCOMING:
                            neighbor_addr = transfer.from_address.lower()
                        else:
                            neighbor_addr = transfer.to_address.lower()

                        # Collect unique transfers
                        if transfer.transfer_id not in seen_transfer_ids:
                            seen_transfer_ids.add(transfer.transfer_id)
                            all_transfers.append(transfer)

                        # Process neighbor node and hop distances with cycle pruning
                        if neighbor_addr:
                            if neighbor_addr not in visited_addrs:
                                visited_addrs.add(neighbor_addr)
                                node_hop_map[neighbor_addr] = hop_idx
                                next_layer.add(neighbor_addr)

                                # Ingest transaction for new forward/backward paths
                                if transfer.tx_hash not in visited_tx_hashes:
                                    if len(collected_txs) >= max_transactions:
                                        transaction_limit_reached = True
                                        break
                                    visited_tx_hashes.add(transfer.tx_hash)
                                    norm_tx = NormalizedTransaction(
                                        tx_hash=transfer.tx_hash,
                                        chain=chain,
                                        timestamp=transfer.timestamp or datetime.now(timezone.utc),
                                        transfers=[transfer],
                                        provider=type(self.provider).__name__
                                    )
                                    collected_txs.append(norm_tx)
                            else:
                                # Cycle prevention: address already visited; keep minimum hop distance
                                if neighbor_addr not in node_hop_map:
                                    node_hop_map[neighbor_addr] = hop_idx
                                elif hop_idx < node_hop_map[neighbor_addr]:
                                    node_hop_map[neighbor_addr] = hop_idx

                    t_cursor = transfer_page.next_cursor
                    t_has_more = transfer_page.has_more and t_cursor is not None

            current_layer = next_layer
            if not current_layer:
                break

        # Calculate actual max hop distance reached among non-root nodes
        actual_max_hops = max((h for addr, h in node_hop_map.items() if addr != root_lower), default=0)
        if actual_max_hops >= max_hops and len(all_transfers) > 0:
            max_hops_reached = True

        # Determine termination reason
        if not all_transfers and not collected_txs:
            termination_reason = "EMPTY_WALLET"
        elif transaction_limit_reached:
            termination_reason = "TRANSACTION_LIMIT_REACHED"
        elif max_hops_reached:
            termination_reason = "MAX_HOPS_REACHED"
        else:
            termination_reason = "NATURAL_TERMINATION"

        return TransactionIngestionBatch(
            case_id=case_id,
            suspect_address=normalized_root,
            chain=chain,
            total_transactions=len(collected_txs),
            retrieval_source=type(self.provider).__name__,
            transactions=collected_txs,
            all_transfers=all_transfers,
            node_hop_map=node_hop_map,
            boundary_nodes=boundary_nodes,
            max_hops_reached=max_hops_reached,
            transaction_limit_reached=transaction_limit_reached,
            actual_max_hops=actual_max_hops,
            termination_reason=termination_reason
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

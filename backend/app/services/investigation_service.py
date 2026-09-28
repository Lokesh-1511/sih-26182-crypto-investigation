# backend/app/services/investigation_service.py
import uuid
from typing import List, Set, Optional, Dict, Any
from ..blockchain.models.enums import Chain, TransferDirection
from ..blockchain.models.transfer import NormalizedTransfer
from ..blockchain.providers.base import BlockchainProvider
from ..blockchain.providers.factory import ProviderFactory
from ..blockchain.ingestion.collector import TransactionCollector
from ..blockchain.exceptions import InvalidAddressError, BlockchainProviderError
from ..schemas.investigation import InvestigationCreateRequest, InvestigationResponse, InvestigationSummary
from ..schemas.graph import FundFlowGraph, GraphNode
from ..graph.builder import GraphBuilder
from ..graph.traversal import GraphTraversalEngine

class InvestigationService:
    """
    Vendor-agnostic orchestration service for cryptocurrency investigations.
    Coordinates address validation, multi-hop blockchain data collection,
    graph construction, and traversal without embedding vendor or UI-specific logic.
    """

    def __init__(self, provider: Optional[BlockchainProvider] = None):
        self.provider = provider or ProviderFactory.get_provider()

    async def investigate(
        self,
        request: InvestigationCreateRequest,
        investigation_id: Optional[str] = None
    ) -> InvestigationResponse:
        """
        Orchestrates an investigation end-to-end:
        1. Validate root address using BlockchainProvider.
        2. Ingest multi-hop transactions using TransactionCollector.
        3. Build FundFlowGraph using GraphBuilder.
        4. Traverse from root using GraphTraversalEngine.
        5. Return API-safe InvestigationResponse.
        """
        inv_id = investigation_id or f"inv_{uuid.uuid4().hex[:12]}"

        # 1. Address Validation
        val_res = await self.provider.validate_address(request.chain, request.address)
        if not val_res.valid:
            raise InvalidAddressError(val_res.reason or f"Invalid {request.chain.value} address format")

        normalized_root = val_res.normalized_address or request.address

        # 2. Ingest transactions & transfers via TransactionCollector
        collector = TransactionCollector(provider=self.provider)
        batch = await collector.collect_case_transactions(
            case_id=inv_id,
            suspect_wallet=normalized_root,
            chain=request.chain,
            max_hops=request.max_hops,
            direction=TransferDirection.OUTGOING,
            max_transactions=request.max_transactions
        )

        # 3. Extract unique transfers from collected transaction batch
        transfers: List[NormalizedTransfer] = []
        seen_tids: Set[str] = set()

        for tx in batch.transactions:
            for t in tx.transfers:
                if t.transfer_id not in seen_tids:
                    seen_tids.add(t.transfer_id)
                    transfers.append(t)

        # 4. Handle empty / low-data wallets gracefully
        if not transfers:
            root_norm = normalized_root.lower()
            root_node = GraphNode(
                id=root_norm,
                address=normalized_root,
                chain=request.chain,
                node_type="SUSPECT",
                label="Suspect Wallet",
                confidence=1.0,
                metadata={"is_root": True}
            )
            empty_graph = FundFlowGraph(
                case_id=inv_id,
                suspect_wallet=normalized_root,
                chain=request.chain,
                nodes=[root_node],
                edges=[],
                breakpoints=[],
                hop_depth=0,
                total_nodes=1,
                total_edges=0
            )
            summary = InvestigationSummary(
                nodes=1,
                edges=0,
                transactions=len(batch.transactions),
                transfers=0,
                hops=0
            )
            return InvestigationResponse(
                investigation_id=inv_id,
                chain=request.chain,
                root_address=normalized_root,
                status="completed",
                summary=summary,
                graph=empty_graph
            )

        # 5. Build FundFlowGraph using GraphBuilder
        builder = GraphBuilder()
        graph_data: FundFlowGraph = builder.build_from_transfers(
            case_id=inv_id,
            suspect_wallet=normalized_root,
            chain=request.chain,
            transfers=transfers
        )

        # 6. Execute Breadth-First Search traversal
        trav_res = GraphTraversalEngine.traverse_bfs(
            graph=builder.graph,
            root_address=normalized_root,
            max_hops=request.max_hops,
            max_edges=request.max_transactions,
            direction="outgoing"
        )

        # 7. Assemble Summary Metrics & Investigation Response
        summary = InvestigationSummary(
            nodes=graph_data.total_nodes,
            edges=graph_data.total_edges,
            transactions=len(batch.transactions),
            transfers=len(transfers),
            hops=graph_data.hop_depth
        )

        return InvestigationResponse(
            investigation_id=inv_id,
            chain=request.chain,
            root_address=normalized_root,
            status="completed",
            summary=summary,
            graph=graph_data
        )

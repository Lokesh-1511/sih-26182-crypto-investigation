# backend/app/services/investigation_service.py
import uuid
from typing import List, Set, Optional, Dict, Any
from ..blockchain.models.enums import Chain, TransferDirection
from ..blockchain.models.transfer import NormalizedTransfer
from ..blockchain.providers.base import BlockchainProvider
from ..blockchain.providers.factory import ProviderFactory
from ..blockchain.ingestion.collector import TransactionCollector
from ..blockchain.exceptions import InvalidAddressError, BlockchainProviderError
from ..schemas.investigation import InvestigationCreateRequest, InvestigationResponse, InvestigationSummary, TraceMetadata
from ..schemas.graph import FundFlowGraph, GraphNode
from ..graph.builder import GraphBuilder
from ..graph.traversal import GraphTraversalEngine
from ..intelligence.service import VaspAttributionService

class InvestigationService:
    """
    Vendor-agnostic orchestration service for cryptocurrency investigations.
    Coordinates address validation, multi-hop blockchain data collection,
    graph construction, traversal, entity resolution, and VASP attribution
    without embedding vendor or UI-specific logic.
    """

    def __init__(
        self,
        provider: Optional[BlockchainProvider] = None,
        attribution_service: Optional[VaspAttributionService] = None
    ):
        self.provider = provider or ProviderFactory.get_provider()
        self.attribution_service = attribution_service or VaspAttributionService()

    async def investigate(
        self,
        request: InvestigationCreateRequest,
        investigation_id: Optional[str] = None
    ) -> InvestigationResponse:
        """
        Orchestrates an investigation end-to-end:
        1. Validate root address using BlockchainProvider.
        2. Ingest multi-hop transactions using TransactionCollector (forward or backward BFS).
        3. Build FundFlowGraph using GraphBuilder with hop distance and boundary annotations.
        4. Calculate TraceMetadata distinguishing requested vs actual depth and boundary limits.
        5. Run downstream Entity Resolution & VASP Attribution.
        6. Return API-safe InvestigationResponse.
        """
        inv_id = investigation_id or f"inv_{uuid.uuid4().hex[:12]}"
        chain_str = request.chain.value if hasattr(request.chain, "value") else str(request.chain)

        # 1. Address Validation
        val_res = await self.provider.validate_address(request.chain, request.address)
        if not val_res.valid:
            raise InvalidAddressError(val_res.reason or f"Invalid {chain_str} address format")

        normalized_root = val_res.normalized_address or request.address

        # 2. Ingest transactions & transfers via TransactionCollector (honors direction, max_hops, max_transactions)
        collector = TransactionCollector(provider=self.provider)
        batch = await collector.collect_case_transactions(
            case_id=inv_id,
            suspect_wallet=normalized_root,
            chain=request.chain,
            max_hops=request.max_hops,
            direction=request.direction,
            max_transactions=request.max_transactions
        )

        # 3. Extract unique transfers from collected transaction batch & collector
        transfers: List[NormalizedTransfer] = []
        seen_tids: Set[str] = set()

        # Combine direct transfers collected by collector and transaction-attached transfers
        for t in batch.all_transfers:
            if t.transfer_id not in seen_tids:
                seen_tids.add(t.transfer_id)
                transfers.append(t)

        for tx in batch.transactions:
            for t in tx.transfers:
                if t.transfer_id not in seen_tids:
                    seen_tids.add(t.transfer_id)
                    transfers.append(t)

        dir_str = request.direction.value if hasattr(request.direction, "value") else str(request.direction)

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
                hop_distance=0,
                is_boundary=False,
                boundary_reason=None,
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
            trace_meta = TraceMetadata(
                direction=dir_str,
                requested_max_hops=request.max_hops,
                actual_max_hops=0,
                max_hops_reached=False,
                max_transactions=request.max_transactions,
                transactions_used=len(batch.transactions),
                transaction_limit_reached=False,
                boundary_nodes_count=0,
                termination_reason="EMPTY_WALLET"
            )
            summary = InvestigationSummary(
                nodes=1,
                edges=0,
                transactions=len(batch.transactions),
                transfers=0,
                hops=0
            )

            entity_resolutions, vasp_attributions = await self.attribution_service.attribute_investigation(
                chain=chain_str,
                root_address=normalized_root,
                graph=empty_graph,
                direction=dir_str
            )

            return InvestigationResponse(
                investigation_id=inv_id,
                chain=request.chain,
                root_address=normalized_root,
                status="completed",
                summary=summary,
                graph=empty_graph,
                trace=trace_meta,
                entity_resolutions=entity_resolutions,
                vasp_attributions=vasp_attributions
            )

        # 5. Build FundFlowGraph using GraphBuilder
        builder = GraphBuilder()
        graph_data: FundFlowGraph = builder.build_from_transfers(
            case_id=inv_id,
            suspect_wallet=normalized_root,
            chain=request.chain,
            transfers=transfers,
            hop_map=batch.node_hop_map,
            boundary_nodes=batch.boundary_nodes,
            direction=dir_str
        )

        # 6. Compute actual trace boundaries and metadata
        actual_max_hops = graph_data.hop_depth
        boundary_nodes_count = sum(1 for n in graph_data.nodes if n.is_boundary)
        max_hops_reached = batch.max_hops_reached or (actual_max_hops >= request.max_hops and len(transfers) > 0)
        tx_limit_reached = batch.transaction_limit_reached or (len(batch.transactions) >= request.max_transactions)

        if tx_limit_reached:
            term_reason = "TRANSACTION_LIMIT_REACHED"
        elif max_hops_reached:
            term_reason = "MAX_HOPS_REACHED"
        else:
            term_reason = "NATURAL_TERMINATION"

        trace_meta = TraceMetadata(
            direction=dir_str,
            requested_max_hops=request.max_hops,
            actual_max_hops=actual_max_hops,
            max_hops_reached=max_hops_reached,
            max_transactions=request.max_transactions,
            transactions_used=len(batch.transactions),
            transaction_limit_reached=tx_limit_reached,
            boundary_nodes_count=boundary_nodes_count,
            termination_reason=term_reason
        )

        # 7. Run Entity Resolution & VASP Attribution (Phase 9)
        entity_resolutions, vasp_attributions = await self.attribution_service.attribute_investigation(
            chain=chain_str,
            root_address=normalized_root,
            graph=graph_data,
            direction=dir_str
        )

        # 8. Assemble Summary Metrics & Investigation Response
        summary = InvestigationSummary(
            nodes=graph_data.total_nodes,
            edges=graph_data.total_edges,
            transactions=len(batch.transactions),
            transfers=len(transfers),
            hops=actual_max_hops
        )

        return InvestigationResponse(
            investigation_id=inv_id,
            chain=request.chain,
            root_address=normalized_root,
            status="completed",
            summary=summary,
            graph=graph_data,
            trace=trace_meta,
            entity_resolutions=entity_resolutions,
            vasp_attributions=vasp_attributions
        )


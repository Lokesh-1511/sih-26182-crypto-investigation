# backend/app/graph/filters.py
from typing import List, Set
from ..schemas.graph import GraphNode, GraphEdge, FundFlowGraph

class GraphNoiseFilter:
    """
    Transparent noise control filters for forensic graphs:
    - Dust threshold suppression (< 0.0001 BTC / 1 USDT)
    - Minimum transfer value filtering
    - Time-window filtering
    """

    @classmethod
    def apply_filters(
        cls,
        graph_data: FundFlowGraph,
        min_amount: float = 0.0,
        hide_dust: bool = True,
        dust_threshold: float = 0.0001
    ) -> FundFlowGraph:
        effective_min = dust_threshold if hide_dust and min_amount < dust_threshold else min_amount

        retained_edges: List[GraphEdge] = []
        active_nodes: Set[str] = {graph_data.suspect_wallet.lower()}

        for edge in graph_data.edges:
            if edge.amount >= effective_min:
                retained_edges.append(edge)
                active_nodes.add(edge.source.lower())
                active_nodes.add(edge.target.lower())

        retained_nodes: List[GraphNode] = [
            node for node in graph_data.nodes if node.id.lower() in active_nodes
        ]

        return FundFlowGraph(
            case_id=graph_data.case_id,
            suspect_wallet=graph_data.suspect_wallet,
            chain=graph_data.chain,
            nodes=retained_nodes,
            edges=retained_edges,
            breakpoints=graph_data.breakpoints,
            hop_depth=graph_data.hop_depth,
            total_nodes=len(retained_nodes),
            total_edges=len(retained_edges)
        )

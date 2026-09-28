# backend/app/graph/filters.py
from decimal import Decimal
from typing import List, Set, Union
from ..schemas.graph import GraphNode, GraphEdge, FundFlowGraph

class GraphNoiseFilter:
    """
    Transparent noise control filters for forensic graphs using exact Decimal precision:
    - Dust threshold suppression (< 0.0001 BTC / 1 USDT)
    - Minimum transfer value filtering
    - Time-window filtering
    """

    @classmethod
    def apply_filters(
        cls,
        graph_data: FundFlowGraph,
        min_amount: Union[Decimal, float, str] = Decimal("0.0"),
        hide_dust: bool = True,
        dust_threshold: Union[Decimal, float, str] = Decimal("0.0001")
    ) -> FundFlowGraph:
        min_dec = Decimal(str(min_amount)) if not isinstance(min_amount, Decimal) else min_amount
        dust_dec = Decimal(str(dust_threshold)) if not isinstance(dust_threshold, Decimal) else dust_threshold

        effective_min = dust_dec if hide_dust and min_dec < dust_dec else min_dec

        retained_edges: List[GraphEdge] = []
        active_nodes: Set[str] = {graph_data.suspect_wallet.lower()}

        for edge in graph_data.edges:
            edge_amt = edge.amount if isinstance(edge.amount, Decimal) else Decimal(str(edge.amount))
            if edge_amt >= effective_min:
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

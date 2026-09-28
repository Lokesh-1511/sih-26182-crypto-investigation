# backend/app/graph/filters.py
from datetime import datetime
from decimal import Decimal
from typing import List, Set, Union, Optional
from ..schemas.graph import GraphNode, GraphEdge, FundFlowGraph

class GraphNoiseFilter:
    """
    Transparent noise control filters for forensic graphs using exact Decimal precision:
    - Dust threshold suppression (< 0.0001 BTC / 0.0001 ETH / 1 USDT)
    - Minimum transfer value filtering
    - Time-window filtering (start_time, end_time)
    - Asset symbol / Asset ID whitelist filtering
    """

    @classmethod
    def apply_filters(
        cls,
        graph_data: FundFlowGraph,
        min_amount: Union[Decimal, float, str] = Decimal("0.0"),
        hide_dust: bool = True,
        dust_threshold: Union[Decimal, float, str] = Decimal("0.0001"),
        asset_filter: Optional[Union[str, List[str]]] = None,
        start_time: Optional[Union[str, datetime]] = None,
        end_time: Optional[Union[str, datetime]] = None
    ) -> FundFlowGraph:
        min_dec = Decimal(str(min_amount)) if not isinstance(min_amount, Decimal) else min_amount
        dust_dec = Decimal(str(dust_threshold)) if not isinstance(dust_threshold, Decimal) else dust_threshold

        effective_min = dust_dec if hide_dust and min_dec < dust_dec else min_dec

        # Asset whitelist set
        allowed_assets: Optional[Set[str]] = None
        if asset_filter:
            if isinstance(asset_filter, str):
                allowed_assets = {asset_filter.upper()}
            else:
                allowed_assets = {a.upper() for a in asset_filter}

        retained_edges: List[GraphEdge] = []
        active_nodes: Set[str] = {graph_data.suspect_wallet.lower()}

        for edge in graph_data.edges:
            # 1. Exact Decimal amount threshold check
            edge_amt = edge.amount if isinstance(edge.amount, Decimal) else Decimal(str(edge.amount))
            if edge_amt < effective_min:
                continue

            # 2. Asset whitelist check
            if allowed_assets:
                edge_sym = edge.asset_symbol.upper()
                edge_aid = edge.asset_id.upper()
                if edge_sym not in allowed_assets and edge_aid not in allowed_assets:
                    continue

            # 3. Timestamp window check
            if (start_time or end_time) and edge.timestamp:
                try:
                    ts = datetime.fromisoformat(edge.timestamp.replace("Z", "+00:00"))
                    if start_time:
                        st = datetime.fromisoformat(start_time.replace("Z", "+00:00")) if isinstance(start_time, str) else start_time
                        if ts < st:
                            continue
                    if end_time:
                        et = datetime.fromisoformat(end_time.replace("Z", "+00:00")) if isinstance(end_time, str) else end_time
                        if ts > et:
                            continue
                except Exception:
                    pass

            retained_edges.append(edge)
            active_nodes.add(edge.source.lower())
            active_nodes.add(edge.target.lower())

        # Retain nodes deterministically: suspect first, then sorted
        suspect_lower = graph_data.suspect_wallet.lower()
        nodes_by_id = {node.id.lower(): node for node in graph_data.nodes if node.id.lower() in active_nodes}

        retained_nodes: List[GraphNode] = []
        if suspect_lower in nodes_by_id:
            retained_nodes.append(nodes_by_id[suspect_lower])

        for nid in sorted(nodes_by_id.keys()):
            if nid != suspect_lower:
                retained_nodes.append(nodes_by_id[nid])

        max_hop = max((e.hop for e in retained_edges), default=0)

        return FundFlowGraph(
            case_id=graph_data.case_id,
            suspect_wallet=graph_data.suspect_wallet,
            chain=graph_data.chain,
            nodes=retained_nodes,
            edges=retained_edges,
            breakpoints=graph_data.breakpoints,
            hop_depth=max(max_hop, 1) if retained_edges else 0,
            total_nodes=len(retained_nodes),
            total_edges=len(retained_edges)
        )

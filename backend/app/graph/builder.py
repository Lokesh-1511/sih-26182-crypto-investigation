# backend/app/graph/builder.py
import networkx as nx
from typing import List, Dict, Any, Optional
from ..schemas.wallet import Chain
from ..schemas.transaction import NormalizedTransaction, NormalizedTransfer
from ..schemas.graph import GraphNode, GraphEdge, FundFlowGraph

class GraphBuilder:
    """
    Constructs a directed NetworkX multigraph from normalized blockchain transfers.
    Preserves transaction hashes, assets, amounts, and hop distances.
    """

    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def build_from_transfers(
        self,
        case_id: str,
        suspect_wallet: str,
        chain: Chain,
        transfers: List[NormalizedTransfer],
        node_labels: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> FundFlowGraph:
        self.graph.clear()
        node_labels = node_labels or {}
        suspect_lower = suspect_wallet.lower()

        # Add nodes and edges
        nodes_dict: Dict[str, GraphNode] = {}
        edges_list: List[GraphEdge] = []

        # Ensure suspect node is present
        nodes_dict[suspect_lower] = GraphNode(
            id=suspect_lower,
            address=suspect_wallet,
            chain=chain,
            node_type="SUSPECT",
            label="Suspect Wallet",
            entity_name=None,
            confidence=1.0
        )
        self.graph.add_node(suspect_lower, **nodes_dict[suspect_lower].model_dump())

        edge_counter = 0
        for t in transfers:
            src = t.from_address.lower()
            dst = t.to_address.lower()

            # Add source node if not seen
            if src not in nodes_dict:
                lbl_info = node_labels.get(src, {})
                nodes_dict[src] = GraphNode(
                    id=src,
                    address=t.from_address,
                    chain=chain,
                    node_type=lbl_info.get("entity_type", "INTERMEDIARY"),
                    label=lbl_info.get("entity_name"),
                    entity_name=lbl_info.get("entity_name"),
                    confidence=lbl_info.get("confidence", 1.0)
                )
                self.graph.add_node(src, **nodes_dict[src].model_dump())

            # Add destination node if not seen
            if dst not in nodes_dict:
                lbl_info = node_labels.get(dst, {})
                nodes_dict[dst] = GraphNode(
                    id=dst,
                    address=t.to_address,
                    chain=chain,
                    node_type=lbl_info.get("entity_type", "INTERMEDIARY"),
                    label=lbl_info.get("entity_name"),
                    entity_name=lbl_info.get("entity_name"),
                    confidence=lbl_info.get("confidence", 1.0)
                )
                self.graph.add_node(dst, **nodes_dict[dst].model_dump())

            # Add edge
            edge_id = f"e_{edge_counter}_{t.tx_id[:8]}"
            edge_counter += 1
            ts_str = t.timestamp.isoformat() if t.timestamp else ""
            edge_obj = GraphEdge(
                id=edge_id,
                source=src,
                target=dst,
                tx_id=t.tx_id,
                asset=t.asset,
                amount=t.amount,
                timestamp=ts_str,
                edge_type="TRANSFER",
                hop=t.hop_distance
            )
            edges_list.append(edge_obj)
            self.graph.add_edge(src, dst, key=edge_id, **edge_obj.model_dump())

        return FundFlowGraph(
            case_id=case_id,
            suspect_wallet=suspect_wallet,
            chain=chain,
            nodes=list(nodes_dict.values()),
            edges=edges_list,
            breakpoints=[],
            hop_depth=3,
            total_nodes=len(nodes_dict),
            total_edges=len(edges_list)
        )

# backend/app/graph/builder.py
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional, Set
import networkx as nx
from ..schemas.wallet import Chain
from ..schemas.transaction import NormalizedTransaction, NormalizedTransfer
from ..schemas.graph import GraphNode, GraphEdge, FundFlowGraph

class GraphBuilder:
    """
    Constructs a directed NetworkX MultiDiGraph from canonical NormalizedTransfer instances.
    
    Architectural Guarantees:
    - Wallet addresses are nodes.
    - Blockchain transfers are individual directed edges with traceable attributes.
    - Multiple transfers between the same pair of nodes are preserved as distinct edges with unique keys.
    - Exact Decimal precision is preserved for financial transfer amounts.
    - Fully provider-agnostic and multi-chain compatible (EVM native, ERC-20, internal calls, UTXO inputs/outputs).
    - Deterministic node and edge serialization.
    """

    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def build_from_transfers(
        self,
        case_id: str,
        suspect_wallet: str,
        chain: Chain,
        transfers: List[NormalizedTransfer],
        node_labels: Optional[Dict[str, Dict[str, Any]]] = None,
        hop_map: Optional[Dict[str, int]] = None
    ) -> FundFlowGraph:
        self.graph.clear()
        node_labels = node_labels or {}
        hop_map = hop_map or {}
        suspect_norm = suspect_wallet.lower()

        nodes_dict: Dict[str, GraphNode] = {}
        edges_list: List[GraphEdge] = []

        # 1. Ensure suspect node is present
        nodes_dict[suspect_norm] = GraphNode(
            id=suspect_norm,
            address=suspect_wallet,
            chain=chain,
            node_type="SUSPECT",
            label="Suspect Wallet",
            entity_name=None,
            confidence=1.0,
            metadata={"is_root": True}
        )
        self.graph.add_node(suspect_norm, **nodes_dict[suspect_norm].model_dump())

        # 2. Add all transfer nodes and edges
        seen_edge_keys: Set[str] = set()

        for t in transfers:
            src = t.from_address.lower()
            dst = t.to_address.lower()

            # Add source node if not present
            if src not in nodes_dict:
                lbl_info = node_labels.get(src, {})
                nodes_dict[src] = GraphNode(
                    id=src,
                    address=t.from_address,
                    chain=chain,
                    node_type=lbl_info.get("entity_type", "INTERMEDIARY"),
                    label=lbl_info.get("entity_name"),
                    entity_name=lbl_info.get("entity_name"),
                    confidence=lbl_info.get("confidence", 1.0),
                    metadata=lbl_info.get("metadata", {})
                )
                self.graph.add_node(src, **nodes_dict[src].model_dump())

            # Add destination node if not present
            if dst not in nodes_dict:
                lbl_info = node_labels.get(dst, {})
                nodes_dict[dst] = GraphNode(
                    id=dst,
                    address=t.to_address,
                    chain=chain,
                    node_type=lbl_info.get("entity_type", "INTERMEDIARY"),
                    label=lbl_info.get("entity_name"),
                    entity_name=lbl_info.get("entity_name"),
                    confidence=lbl_info.get("confidence", 1.0),
                    metadata=lbl_info.get("metadata", {})
                )
                self.graph.add_node(dst, **nodes_dict[dst].model_dump())

            # Determine deterministic edge key
            edge_key = t.transfer_id
            if not edge_key or edge_key in seen_edge_keys:
                edge_key = f"{t.tx_hash}_{t.transfer_index}"
                if edge_key in seen_edge_keys:
                    edge_key = f"{edge_key}_{len(seen_edge_keys)}"
            seen_edge_keys.add(edge_key)

            # Decimal amount handling
            exact_amt = t.normalized_amount if isinstance(t.normalized_amount, Decimal) else Decimal(str(t.amount))

            # Hop distance: prefer explicit hop_map, then transfer hop_distance, default 1
            hop_val = hop_map.get(dst, getattr(t, "hop_distance", 1))
            if hop_val == 0 and dst != suspect_norm:
                hop_val = 1

            # Transfer type string normalized to uppercase
            if hasattr(t.transfer_type, "value"):
                t_type_str = str(t.transfer_type.value).upper()
            else:
                t_type_str = str(t.transfer_type).upper()

            # Evidence reference
            ev_ref = t.evidence_ref or f"ev_{t.tx_hash[:10]}"

            ts_str = t.timestamp.isoformat() if t.timestamp else ""

            edge_obj = GraphEdge(
                id=edge_key,
                transfer_id=t.transfer_id or edge_key,
                tx_hash=t.tx_hash,
                source=src,
                target=dst,
                asset_id=t.asset_id or t.asset_symbol or "ETH",
                asset_symbol=t.asset_symbol or "ETH",
                amount=exact_amt,
                timestamp=ts_str,
                transfer_type=t_type_str,
                edge_type="SWEEP" if getattr(t, "is_sweep", False) else "TRANSFER",
                hop=hop_val,
                evidence_ref=ev_ref
            )
            edges_list.append(edge_obj)

            # Store in MultiDiGraph with unique edge_key
            self.graph.add_edge(src, dst, key=edge_key, **edge_obj.model_dump())

        # 3. Dynamic shortest-path hop computation if hops were not preset
        for edge_obj in edges_list:
            if edge_obj.hop == 1 and edge_obj.source != suspect_norm:
                try:
                    shortest = nx.shortest_path_length(self.graph, source=suspect_norm, target=edge_obj.target)
                    edge_obj.hop = shortest
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    pass

        # 4. Deterministic sorting
        # Suspect node first, followed by alphabetical sort of remaining nodes
        sorted_nodes: List[GraphNode] = [nodes_dict[suspect_norm]] + sorted(
            [n for k, n in nodes_dict.items() if k != suspect_norm],
            key=lambda x: x.id
        )

        # Edges sorted deterministically by (timestamp, tx_hash, transfer_id)
        sorted_edges: List[GraphEdge] = sorted(
            edges_list,
            key=lambda e: (e.timestamp or "", e.tx_hash, e.transfer_id)
        )

        max_hop = max((e.hop for e in sorted_edges), default=0)

        return FundFlowGraph(
            case_id=case_id,
            suspect_wallet=suspect_wallet,
            chain=chain,
            nodes=sorted_nodes,
            edges=sorted_edges,
            breakpoints=[],
            hop_depth=max(max_hop, 1) if sorted_edges else 0,
            total_nodes=len(sorted_nodes),
            total_edges=len(sorted_edges)
        )

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Calculates volume sums by asset using exact Decimal precision."""
        asset_volumes: Dict[str, Decimal] = {}
        for _, _, data in self.graph.edges(data=True):
            sym = data.get("asset_symbol", "UNKNOWN")
            amt = data.get("amount", Decimal("0"))
            if not isinstance(amt, Decimal):
                amt = Decimal(str(amt))
            asset_volumes[sym] = asset_volumes.get(sym, Decimal("0")) + amt

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "asset_volumes": asset_volumes
        }

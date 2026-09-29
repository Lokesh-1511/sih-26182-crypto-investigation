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
        hop_map: Optional[Dict[str, int]] = None,
        boundary_nodes: Optional[Dict[str, str]] = None,
        direction: str = "outgoing"
    ) -> FundFlowGraph:
        self.graph.clear()
        node_labels = node_labels or {}
        hop_map = hop_map or {}
        boundary_nodes = boundary_nodes or {}
        suspect_norm = suspect_wallet.lower()
        is_incoming = direction.lower() in ("incoming", "in", "backward")

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
            hop_distance=0,
            is_boundary=False,
            boundary_reason=None,
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
                src_is_bnd = src in boundary_nodes
                src_bnd_reason = boundary_nodes.get(src)
                src_hop = hop_map.get(src, 0 if src == suspect_norm else 1)
                nodes_dict[src] = GraphNode(
                    id=src,
                    address=t.from_address,
                    chain=chain,
                    node_type=lbl_info.get("entity_type", "INTERMEDIARY"),
                    label=lbl_info.get("entity_name"),
                    entity_name=lbl_info.get("entity_name"),
                    confidence=lbl_info.get("confidence", 1.0),
                    hop_distance=src_hop,
                    is_boundary=src_is_bnd,
                    boundary_reason=src_bnd_reason,
                    metadata=lbl_info.get("metadata", {})
                )
                self.graph.add_node(src, **nodes_dict[src].model_dump())
            else:
                # Update hop distance if better or in hop_map
                if src in hop_map:
                    nodes_dict[src].hop_distance = hop_map[src]
                if src in boundary_nodes:
                    nodes_dict[src].is_boundary = True
                    nodes_dict[src].boundary_reason = boundary_nodes[src]

            # Add destination node if not present
            if dst not in nodes_dict:
                lbl_info = node_labels.get(dst, {})
                dst_is_bnd = dst in boundary_nodes
                dst_bnd_reason = boundary_nodes.get(dst)
                dst_hop = hop_map.get(dst, 0 if dst == suspect_norm else 1)
                nodes_dict[dst] = GraphNode(
                    id=dst,
                    address=t.to_address,
                    chain=chain,
                    node_type=lbl_info.get("entity_type", "INTERMEDIARY"),
                    label=lbl_info.get("entity_name"),
                    entity_name=lbl_info.get("entity_name"),
                    confidence=lbl_info.get("confidence", 1.0),
                    hop_distance=dst_hop,
                    is_boundary=dst_is_bnd,
                    boundary_reason=dst_bnd_reason,
                    metadata=lbl_info.get("metadata", {})
                )
                self.graph.add_node(dst, **nodes_dict[dst].model_dump())
            else:
                if dst in hop_map:
                    nodes_dict[dst].hop_distance = hop_map[dst]
                if dst in boundary_nodes:
                    nodes_dict[dst].is_boundary = True
                    nodes_dict[dst].boundary_reason = boundary_nodes[dst]

            # Determine deterministic edge key
            edge_key = t.transfer_id
            if not edge_key or edge_key in seen_edge_keys:
                edge_key = f"{t.tx_hash}_{t.transfer_index}"
                if edge_key in seen_edge_keys:
                    edge_key = f"{edge_key}_{len(seen_edge_keys)}"
            seen_edge_keys.add(edge_key)

            # Decimal amount handling
            exact_amt = t.normalized_amount if isinstance(t.normalized_amount, Decimal) else Decimal(str(t.amount))

            # Direction-aware hop distance assignment
            if is_incoming:
                # In incoming flow, hop distance increases moving backwards to source
                hop_val = hop_map.get(src, getattr(t, "hop_distance", 1))
            else:
                # In outgoing flow, hop distance increases moving forwards to target
                hop_val = hop_map.get(dst, getattr(t, "hop_distance", 1))

            if hop_val == 0 and (dst != suspect_norm if not is_incoming else src != suspect_norm):
                hop_val = 1

            edge_is_bnd = (src in boundary_nodes or dst in boundary_nodes)

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
                is_boundary=edge_is_bnd,
                evidence_ref=ev_ref
            )
            edges_list.append(edge_obj)

            # Store in MultiDiGraph with unique edge_key (always preserves source -> target blockchain fund direction)
            self.graph.add_edge(src, dst, key=edge_key, **edge_obj.model_dump())

        # 3. Dynamic shortest-path hop computation if hop_map was empty
        if not hop_map and len(nodes_dict) > 1:
            for node_id, node_obj in nodes_dict.items():
                if node_id == suspect_norm:
                    continue
                try:
                    if is_incoming:
                        dist = nx.shortest_path_length(self.graph, source=node_id, target=suspect_norm)
                    else:
                        dist = nx.shortest_path_length(self.graph, source=suspect_norm, target=node_id)
                    node_obj.hop_distance = dist
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

        actual_hop_depth = max((n.hop_distance for n in sorted_nodes if not n.is_boundary), default=0)
        if actual_hop_depth == 0 and sorted_edges:
            actual_hop_depth = 1

        return FundFlowGraph(
            case_id=case_id,
            suspect_wallet=suspect_wallet,
            chain=chain,
            nodes=sorted_nodes,
            edges=sorted_edges,
            breakpoints=[],
            hop_depth=actual_hop_depth,
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

# backend/app/graph/traversal.py
from collections import deque
from typing import List, Dict, Set, Tuple, Any, Optional
import networkx as nx

class GraphTraversalEngine:
    """
    Traverses the directed fund-flow MultiDiGraph up to a configurable hop depth (1 to 5 hops).
    Handles cyclic transactions, preserves distinct multi-edges between the same node pair,
    and supports node/edge traversal limits.
    """

    @classmethod
    def traverse_bfs(
        cls,
        graph: nx.MultiDiGraph,
        root_address: str,
        max_hops: int = 4,
        max_edges: Optional[int] = None,
        max_nodes: Optional[int] = None,
        direction: str = "outgoing"
    ) -> Dict[str, Any]:
        root = root_address.lower()
        if root not in graph:
            return {
                "visited_nodes": [],
                "hop_layers": {},
                "paths": [],
                "edges": [],
                "max_depth_reached": 0,
                "total_edges_traversed": 0
            }

        visited_nodes: Set[str] = {root}
        queue: deque = deque([(root, 0, [root])])
        hop_layers: Dict[int, List[str]] = {0: [root]}
        all_paths: List[List[str]] = []
        traversed_edges: List[Dict[str, Any]] = []
        seen_edge_keys: Set[str] = set()

        while queue:
            if max_nodes and len(visited_nodes) >= max_nodes:
                break
            if max_edges and len(traversed_edges) >= max_edges:
                break

            current, depth, path = queue.popleft()

            if depth >= max_hops:
                all_paths.append(path)
                continue

            # Resolve adjacent nodes and edge data based on direction
            adjacent_items = []
            if direction in ("outgoing", "any"):
                # Outgoing edges from current
                for target, edge_dict in graph.adj.get(current, {}).items():
                    for edge_key, data in edge_dict.items():
                        adjacent_items.append((current, target, edge_key, data, "OUT"))

            if direction in ("incoming", "any"):
                # Incoming edges to current
                if hasattr(graph, "pred"):
                    for source, edge_dict in graph.pred.get(current, {}).items():
                        for edge_key, data in edge_dict.items():
                            adjacent_items.append((source, current, edge_key, data, "IN"))

            if not adjacent_items:
                all_paths.append(path)
                continue

            for u, v, edge_key, edge_data, edge_dir in adjacent_items:
                if max_edges and len(traversed_edges) >= max_edges:
                    break

                # Next node along exploration direction
                nxt = v if edge_dir == "OUT" else u

                # Record edge if not already recorded
                unique_edge_id = f"{u}->{v}:{edge_key}"
                if unique_edge_id not in seen_edge_keys:
                    seen_edge_keys.add(unique_edge_id)
                    edge_record = dict(edge_data)
                    edge_record["_traversal_source"] = u
                    edge_record["_traversal_target"] = v
                    edge_record["_edge_key"] = edge_key
                    traversed_edges.append(edge_record)

                # Cycle check in current branch path
                if nxt not in path:
                    new_path = path + [nxt]
                    all_paths.append(new_path)

                    if nxt not in visited_nodes:
                        if max_nodes and len(visited_nodes) >= max_nodes:
                            break
                        visited_nodes.add(nxt)
                        next_depth = depth + 1
                        if next_depth not in hop_layers:
                            hop_layers[next_depth] = []
                        hop_layers[next_depth].append(nxt)
                        queue.append((nxt, next_depth, new_path))

        return {
            "visited_nodes": list(visited_nodes),
            "hop_layers": hop_layers,
            "paths": all_paths,
            "edges": traversed_edges,
            "max_depth_reached": max(hop_layers.keys()) if hop_layers else 0,
            "total_edges_traversed": len(traversed_edges)
        }

    @classmethod
    def extract_subgraph(
        cls,
        graph: nx.MultiDiGraph,
        root_address: str,
        max_hops: int = 4,
        max_edges: Optional[int] = None,
        max_nodes: Optional[int] = None,
        direction: str = "outgoing"
    ) -> nx.MultiDiGraph:
        """Extracts a scoped MultiDiGraph based on traversal parameters."""
        trav_res = cls.traverse_bfs(
            graph=graph,
            root_address=root_address,
            max_hops=max_hops,
            max_edges=max_edges,
            max_nodes=max_nodes,
            direction=direction
        )

        subgraph = nx.MultiDiGraph()
        for node_id in trav_res["visited_nodes"]:
            if graph.has_node(node_id):
                subgraph.add_node(node_id, **graph.nodes[node_id])

        for edge_info in trav_res["edges"]:
            u = edge_info["_traversal_source"]
            v = edge_info["_traversal_target"]
            key = edge_info["_edge_key"]
            # Clean internal traversal metadata
            edge_data = {k: val for k, val in edge_info.items() if not k.startswith("_")}
            subgraph.add_edge(u, v, key=key, **edge_data)

        return subgraph

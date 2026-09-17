# backend/app/graph/traversal.py
from collections import deque
from typing import List, Dict, Set, Tuple, Any
import networkx as nx

class GraphTraversalEngine:
    """
    Traverses the directed fund-flow graph up to a configurable hop depth (3 to 5 hops).
    Handles cyclic transactions and extracts downstream exploration paths.
    """

    @classmethod
    def traverse_bfs(
        cls,
        graph: nx.MultiDiGraph,
        root_address: str,
        max_hops: int = 4
    ) -> Dict[str, Any]:
        root = root_address.lower()
        if root not in graph:
            return {"visited_nodes": [], "hop_layers": {}, "paths": []}

        visited: Set[str] = {root}
        queue: deque = deque([(root, 0, [root])])
        hop_layers: Dict[int, List[str]] = {0: [root]}
        all_paths: List[List[str]] = []

        while queue:
            current, depth, path = queue.popleft()
            if depth >= max_hops:
                all_paths.append(path)
                continue

            successors = list(graph.successors(current))
            if not successors:
                all_paths.append(path)
                continue

            for nxt in successors:
                # Cycle check in current branch path
                if nxt not in path:
                    new_path = path + [nxt]
                    all_paths.append(new_path)
                    if nxt not in visited:
                        visited.add(nxt)
                        next_depth = depth + 1
                        if next_depth not in hop_layers:
                            hop_layers[next_depth] = []
                        hop_layers[next_depth].append(nxt)
                        queue.append((nxt, next_depth, new_path))

        return {
            "visited_nodes": list(visited),
            "hop_layers": hop_layers,
            "paths": all_paths,
            "max_depth_reached": max(hop_layers.keys()) if hop_layers else 0
        }

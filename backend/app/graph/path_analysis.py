# backend/app/graph/path_analysis.py
from typing import List, Dict, Any, Optional
import networkx as nx

class PathAnalysisEngine:
    """
    Computes forensic paths across fund-flow graphs:
    - Shortest path to any VASP node
    - Strongest-value path (maximum cumulative value transfer)
    """

    @classmethod
    def find_shortest_path(
        cls,
        graph: nx.MultiDiGraph,
        source: str,
        target: str
    ) -> Optional[List[str]]:
        src = source.lower()
        dst = target.lower()
        try:
            return nx.shortest_path(graph, source=src, target=dst)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    @classmethod
    def find_highest_value_path(
        cls,
        graph: nx.MultiDiGraph,
        source: str,
        target: str
    ) -> Optional[List[str]]:
        """
        Uses inverted weight to find the path carrying the highest single bottleneck volume.
        """
        src = source.lower()
        dst = target.lower()
        if not graph.has_node(src) or not graph.has_node(dst):
            return None

        # Convert to DiGraph with min cost = 1 / max_amount
        simple_digraph = nx.DiGraph()
        for u, v, data in graph.edges(data=True):
            amt = float(data.get("amount", 0.00001))
            weight = 1.0 / (amt if amt > 0 else 0.00001)
            if simple_digraph.has_edge(u, v):
                if weight < simple_digraph[u][v]["weight"]:
                    simple_digraph[u][v]["weight"] = weight
            else:
                simple_digraph.add_edge(u, v, weight=weight)

        try:
            return nx.dijkstra_path(simple_digraph, source=src, target=dst, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

# backend/app/risk/breakpoint.py
from typing import List, Dict, Any, Optional
from ..schemas.graph import FundFlowGraph, ObfuscationBreakpoint

class ObfuscationBreakpointDetector:
    """
    Detects structural and behavioral shifts along fund flows:
    - Rapid 1-to-N fan-out
    - High-frequency relay hops
    - Direct mixer / bridge interactions
    """

    @classmethod
    def detect_breakpoints(
        cls,
        graph_data: FundFlowGraph,
        fan_out_threshold: int = 3
    ) -> List[ObfuscationBreakpoint]:
        breakpoints: List[ObfuscationBreakpoint] = []
        out_degrees: Dict[str, List[str]] = {}

        for edge in graph_data.edges:
            src = edge.source.lower()
            if src not in out_degrees:
                out_degrees[src] = []
            out_degrees[src].append(edge.tx_id)

        for node in graph_data.nodes:
            addr_lower = node.id.lower()
            signals = []
            reason_parts = []
            tx_ids = out_degrees.get(addr_lower, [])

            # 1. Fan-out detection
            if len(tx_ids) >= fan_out_threshold and node.node_type != "SUSPECT":
                signals.append("ANOMALOUS_FAN_OUT")
                reason_parts.append(f"Sudden fan-out into {len(tx_ids)} parallel recipient addresses")

            # 2. Bridge or Mixer interaction
            if node.node_type in ("MIXER", "BRIDGE"):
                signals.append(f"DIRECT_{node.node_type}_INTERACTION")
                reason_parts.append(f"Flow intersects known {node.node_type.lower()} contract infrastructure")

            if signals:
                bp = ObfuscationBreakpoint(
                    node_id=node.id,
                    address=node.address,
                    breakpoint_type=signals[0],
                    severity="HIGH" if "MIXER" in str(signals) else "MEDIUM",
                    signals_detected=signals,
                    reasoning="; ".join(reason_parts),
                    supporting_tx_ids=tx_ids
                )
                node.is_breakpoint = True
                node.breakpoint_details = bp
                breakpoints.append(bp)

        return breakpoints

# backend/app/intelligence/service.py
from typing import List, Dict, Tuple, Optional, Set
from collections import deque
from .models import EntityResolution, VaspAttribution, EntityType, ResolutionStatus
from .resolver import EntityResolver
from ..schemas.graph import FundFlowGraph, GraphNode, GraphEdge

class VaspAttributionService:
    """
    Downstream service that consumes investigation graph results,
    resolves discovered addresses against address intelligence providers,
    and constructs path-aware VASP attributions without modifying canonical blockchain data.
    """

    def __init__(self, resolver: Optional[EntityResolver] = None):
        self.resolver = resolver or EntityResolver()

    def _compute_path_and_transfers(
        self,
        root_address: str,
        target_address: str,
        edges: List[GraphEdge],
        direction: str
    ) -> Tuple[List[str], List[str]]:
        """
        Computes the ordered address path and associated transfer IDs from root to target
        along the traversal direction.
        - In outgoing traces: follows source -> target
        - In incoming traces: follows target -> source (predecessor flow)
        """
        root_norm = root_address.lower()
        target_norm = target_address.lower()

        if root_norm == target_norm:
            return [root_address], []

        is_incoming = str(direction).lower() in ("incoming", "in", "backward")

        # Queue contains (current_address_norm, path_addresses, path_transfer_ids)
        queue = deque([(root_norm, [root_address], [])])
        visited = {root_norm}

        while queue:
            curr_norm, path, transfer_ids = queue.popleft()

            if curr_norm == target_norm:
                return path, transfer_ids

            # Find matching outgoing edges along traversal flow
            for e in edges:
                src_norm = e.source.lower()
                tgt_norm = e.target.lower()

                if is_incoming:
                    # In incoming trace, funds flowed from predecessor into current address: e.target == curr
                    if tgt_norm == curr_norm and src_norm not in visited:
                        visited.add(src_norm)
                        queue.append((
                            src_norm,
                            path + [e.source],
                            transfer_ids + [e.transfer_id]
                        ))
                else:
                    # In outgoing trace, funds flowed from current into next address: e.source == curr
                    if src_norm == curr_norm and tgt_norm not in visited:
                        visited.add(tgt_norm)
                        queue.append((
                            tgt_norm,
                            path + [e.target],
                            transfer_ids + [e.transfer_id]
                        ))

        # Fallback if disconnected or beyond traversal scope
        return [root_address, target_address], []

    async def attribute_investigation(
        self,
        chain: str,
        root_address: str,
        graph: FundFlowGraph,
        direction: str = "outgoing"
    ) -> Tuple[List[EntityResolution], List[VaspAttribution]]:
        """
        Resolves entities for all discovered graph nodes and generates structured VASP attributions.
        Also annotates graph nodes with resolved entity information for UI rendering.
        """
        if not graph or not graph.nodes:
            return [], []

        # 1. Collect all discovered addresses from graph nodes
        addresses_to_resolve = [node.address for node in graph.nodes if node.address]

        # 2. Batch resolve via EntityResolver
        resolutions_map: Dict[str, EntityResolution] = await self.resolver.resolve_addresses(
            chain=chain,
            addresses=addresses_to_resolve
        )

        entity_resolutions: List[EntityResolution] = list(resolutions_map.values())
        vasp_attributions: List[VaspAttribution] = []

        # 3. Enrich Graph Nodes and construct VaspAttributions
        for node in graph.nodes:
            addr_key = node.address.lower() if chain.lower() in ("eth", "ethereum", "polygon", "arbitrum", "bsc") else node.address
            # Match resolution
            resolution = resolutions_map.get(node.address) or resolutions_map.get(addr_key)

            if resolution and resolution.resolution_status == ResolutionStatus.RESOLVED:
                # Update GraphNode entity metadata
                node.entity_name = resolution.entity_name
                if resolution.entity_type:
                    node.metadata["entity_type"] = resolution.entity_type.value
                    node.metadata["is_vasp"] = resolution.vasp_status
                    node.metadata["source"] = resolution.source
                    node.metadata["source_reference"] = resolution.source_reference

                # If entity is a VASP or Exchange, create a path-aware VaspAttribution
                if resolution.vasp_status:
                    path, transfer_ids = self._compute_path_and_transfers(
                        root_address=root_address,
                        target_address=node.address,
                        edges=graph.edges,
                        direction=direction
                    )

                    attribution = VaspAttribution(
                        address=node.address,
                        chain=chain,
                        entity_id=resolution.entity_id or f"vasp_{node.address[:8]}",
                        entity_name=resolution.entity_name or "Unknown VASP",
                        entity_type=resolution.entity_type or EntityType.VASP,
                        vasp_status=True,
                        hop_distance=node.hop_distance,
                        direction=direction,
                        path=path,
                        resolution_status=ResolutionStatus.RESOLVED,
                        source=resolution.source or "local_registry",
                        source_reference=resolution.source_reference or "registry://verified",
                        relevant_transfer_ids=transfer_ids
                    )
                    vasp_attributions.append(attribution)
            elif resolution and resolution.resolution_status == ResolutionStatus.AMBIGUOUS:
                node.entity_name = "Multiple candidates"
                node.metadata["resolution_status"] = "AMBIGUOUS"
                node.metadata["candidates_count"] = len(resolution.candidates)

        # 4. Sort deterministically
        entity_resolutions.sort(key=lambda r: r.address)
        vasp_attributions.sort(key=lambda a: (a.hop_distance, a.address, a.direction))

        return entity_resolutions, vasp_attributions

# backend/app/evidence/builder.py
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from ..schemas.evidence import EvidenceItem, EvidenceClass, EvidenceType, CaseDossier, compute_dossier_sha256
from ..schemas.investigation import InvestigationResponse, InvestigationSummary, TraceMetadata
from ..schemas.graph import FundFlowGraph, GraphNode, GraphEdge
from ..intelligence.models import EntityResolution, VaspAttribution

class EvidenceBuilder:
    """
    Constructs canonical, forensic evidence records and reproducible case dossiers
    from multi-hop fund-flow investigation results.
    Preserves exact Decimal amounts and explicit provenance tracking.
    """

    @classmethod
    def build_evidence_items(
        cls,
        investigation: InvestigationResponse
    ) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []
        inv_id = investigation.investigation_id
        chain_val = investigation.chain.value if hasattr(investigation.chain, "value") else str(investigation.chain)

        # 1. Trace Summary Evidence (DERIVED)
        if investigation.trace:
            t = investigation.trace
            items.append(
                EvidenceItem(
                    evidence_id=f"ev_trace_{inv_id[:8]}",
                    evidence_class=EvidenceClass.DERIVED,
                    evidence_type=EvidenceType.TRACE_SUMMARY.value,
                    title=f"Trace Execution: {t.termination_reason}",
                    description=(
                        f"Multi-hop trace on {chain_val.upper()} terminated with reason '{t.termination_reason}'. "
                        f"Traversed {t.actual_max_hops} of {t.requested_max_hops} requested hops. "
                        f"Ingested {t.transactions_used} on-chain transactions."
                    ),
                    source="GRAPH_ENGINE",
                    source_reference=inv_id,
                    hop_distance=t.actual_max_hops,
                    confidence_qualification="DETERMINISTIC_EXECUTION",
                    provenance_metadata={
                        "direction": t.direction,
                        "requested_max_hops": t.requested_max_hops,
                        "actual_max_hops": t.actual_max_hops,
                        "transactions_used": t.transactions_used,
                        "termination_reason": t.termination_reason
                    }
                )
            )

        # 2. Observed On-Chain Transfers (OBSERVED)
        if investigation.graph and investigation.graph.edges:
            for idx, edge in enumerate(investigation.graph.edges):
                edge_id = edge.id or f"edge_{idx}"
                tx_short = edge.tx_hash[:10] if edge.tx_hash else f"tx{idx}"
                ev_id = f"ev_tx_{tx_short}_{idx}"
                
                # Format timestamp safely
                ts = None
                if edge.timestamp:
                    try:
                        if isinstance(edge.timestamp, str):
                            ts = datetime.fromisoformat(edge.timestamp.replace("Z", "+00:00"))
                        elif isinstance(edge.timestamp, datetime):
                            ts = edge.timestamp
                    except Exception:
                        ts = None

                src = edge.source
                tgt = edge.target
                amt = str(edge.amount)
                symbol = edge.asset_symbol or edge.asset_id or "CRYPTO"
                hop = edge.hop if edge.hop is not None else 1

                items.append(
                    EvidenceItem(
                        evidence_id=ev_id,
                        evidence_class=EvidenceClass.OBSERVED,
                        evidence_type=EvidenceType.TRANSFER_OBSERVED.value,
                        title=f"On-Chain Transfer: {amt} {symbol}",
                        description=f"Observed on-chain transfer of {amt} {symbol} from {src} to {tgt} in transaction {edge.tx_hash} at hop {hop}.",
                        source="BITQUERY_V2",
                        source_reference=edge.tx_hash,
                        tx_hash=edge.tx_hash,
                        transfer_id=edge.transfer_id,
                        source_address=src,
                        destination_address=tgt,
                        asset=symbol,
                        amount=amt,
                        timestamp=ts,
                        hop_distance=hop,
                        graph_relationship=f"HOP_{max(0, hop - 1)}->HOP_{hop}",
                        confidence_qualification="ON_CHAIN_VERIFIED",
                        provenance_metadata={
                            "edge_id": edge_id,
                            "transfer_type": edge.transfer_type,
                            "is_boundary": edge.is_boundary
                        }
                    )
                )

        # 3. Entity Resolutions (RESOLVED or UNKNOWN)
        if investigation.entity_resolutions:
            for res in investigation.entity_resolutions:
                addr_short = res.address[:10]
                if res.resolution_status == "RESOLVED":
                    items.append(
                        EvidenceItem(
                            evidence_id=f"ev_ent_{addr_short}",
                            evidence_class=EvidenceClass.RESOLVED,
                            evidence_type=EvidenceType.ENTITY_RESOLVED.value,
                            title=f"Entity Resolution: {res.entity_name}",
                            description=(
                                f"Address {res.address} verified as known entity '{res.entity_name}' "
                                f"(type: {res.entity_type}, VASP: {res.vasp_status}) via {res.source or 'INTELLIGENCE_REGISTRY'}."
                            ),
                            source=res.source or "INTELLIGENCE_REGISTRY",
                            source_reference=res.source_reference,
                            source_address=res.address,
                            entity_association=res.entity_name,
                            confidence_qualification="REGISTRY_VERIFIED_MATCH",
                            provenance_metadata={
                                "entity_id": res.entity_id,
                                "entity_type": str(res.entity_type),
                                "vasp_status": res.vasp_status,
                                "resolved_at": res.resolved_at.isoformat() if hasattr(res.resolved_at, "isoformat") else str(res.resolved_at)
                            }
                        )
                    )
                else:
                    items.append(
                        EvidenceItem(
                            evidence_id=f"ev_unres_{addr_short}",
                            evidence_class=EvidenceClass.UNKNOWN,
                            evidence_type=EvidenceType.UNRESOLVED_ADDRESS.value,
                            title=f"Unresolved Address: {res.address[:14]}...",
                            description=f"Address {res.address} has no matching records in configured intelligence registries.",
                            source="INTELLIGENCE_REGISTRY",
                            source_address=res.address,
                            confidence_qualification="NO_KNOWN_ATTRIBUTION",
                            provenance_metadata={"status": res.resolution_status}
                        )
                    )

        # 4. VASP Attributions (DERIVED for hop 1, INFERRED for multi-hop)
        if investigation.vasp_attributions:
            for vasp in investigation.vasp_attributions:
                vasp_short = vasp.entity_id
                addr_short = vasp.address[:8]
                ev_class = EvidenceClass.DERIVED if vasp.hop_distance == 1 else EvidenceClass.INFERRED
                path_str = " -> ".join(vasp.path) if vasp.path else f"root -> {vasp.address}"

                items.append(
                    EvidenceItem(
                        evidence_id=f"ev_vasp_{vasp_short}_{addr_short}",
                        evidence_class=ev_class,
                        evidence_type=EvidenceType.VASP_ATTRIBUTED.value,
                        title=f"VASP Attribution: {vasp.entity_name} ({vasp.hop_distance} hops)",
                        description=(
                            f"Fund flow path connects root wallet to {vasp.entity_name} ({vasp.entity_type}) "
                            f"at terminal infrastructure address {vasp.address} over {vasp.hop_distance} hops. Path: {path_str}."
                        ),
                        source=vasp.source,
                        source_reference=vasp.source_reference,
                        destination_address=vasp.address,
                        hop_distance=vasp.hop_distance,
                        entity_association=vasp.entity_name,
                        vasp_association=vasp.entity_name,
                        confidence_qualification=f"TOPOLOGICAL_PROXIMITY_HOP_{vasp.hop_distance}",
                        provenance_metadata={
                            "entity_id": vasp.entity_id,
                            "path": vasp.path,
                            "relevant_transfers": vasp.relevant_transfer_ids
                        }
                    )
                )

        return items

    @classmethod
    def build_case_dossier(
        cls,
        investigation: InvestigationResponse
    ) -> CaseDossier:
        """
        Creates a complete forensic CaseDossier with calculated deterministic SHA-256 digest.
        """
        evidence_items = cls.build_evidence_items(investigation)
        inv_id = investigation.investigation_id
        chain_val = investigation.chain.value if hasattr(investigation.chain, "value") else str(investigation.chain)

        dossier_data: Dict[str, Any] = {
            "dossier_id": f"dos_{inv_id}",
            "investigation_id": inv_id,
            "chain": chain_val,
            "root_wallet": investigation.root_address,
            "direction": investigation.trace.direction if investigation.trace else "outgoing",
            "requested_max_hops": investigation.trace.requested_max_hops if investigation.trace else 1,
            "actual_depth_reached": investigation.summary.hops,
            "trace_termination_reason": investigation.trace.termination_reason if investigation.trace else "COMPLETED",
            "summary": investigation.summary.model_dump(),
            "nodes_count": investigation.summary.nodes,
            "edges_count": investigation.summary.edges,
            "transactions_count": investigation.summary.transactions,
            "transfers_count": investigation.summary.transfers,
            "entity_resolutions": [r.model_dump() for r in (investigation.entity_resolutions or [])],
            "vasp_attributions": [v.model_dump() for v in (investigation.vasp_attributions or [])],
            "evidence_items": [e.model_dump() for e in evidence_items],
            "operator_vs_beneficiary_notice": (
                "OPERATOR VS BENEFICIARY QUALIFICATION: Association reflects on-chain fund-flow path connection to infrastructure. "
                "Public blockchain evidence alone does not establish natural person beneficiary identity without lawful off-chain KYC records."
            ),
            "limitations_disclaimer": (
                "INVESTIGATIVE DISCLAIMER: Findings represent observed ledger transfers and algorithmic entity matching. "
                "Heuristic inference is qualified and subject to off-chain legal verification."
            ),
            "generated_at": datetime.now(timezone.utc)
        }

        # Calculate deterministic SHA-256 hash over canonical representation
        sha256_hash = compute_dossier_sha256(dossier_data)
        dossier_data["dossier_hash_sha256"] = sha256_hash

        return CaseDossier(
            dossier_id=dossier_data["dossier_id"],
            investigation_id=dossier_data["investigation_id"],
            chain=dossier_data["chain"],
            root_wallet=dossier_data["root_wallet"],
            direction=dossier_data["direction"],
            requested_max_hops=dossier_data["requested_max_hops"],
            actual_depth_reached=dossier_data["actual_depth_reached"],
            trace_termination_reason=dossier_data["trace_termination_reason"],
            summary=investigation.summary,
            nodes_count=dossier_data["nodes_count"],
            edges_count=dossier_data["edges_count"],
            transactions_count=dossier_data["transactions_count"],
            transfers_count=dossier_data["transfers_count"],
            entity_resolutions=investigation.entity_resolutions or [],
            vasp_attributions=investigation.vasp_attributions or [],
            evidence_items=evidence_items,
            operator_vs_beneficiary_notice=dossier_data["operator_vs_beneficiary_notice"],
            limitations_disclaimer=dossier_data["limitations_disclaimer"],
            generated_at=dossier_data["generated_at"],
            dossier_hash_sha256=sha256_hash
        )

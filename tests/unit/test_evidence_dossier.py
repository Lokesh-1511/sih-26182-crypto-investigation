# tests/unit/test_evidence_dossier.py
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.investigation import (
    InvestigationResponse,
    InvestigationSummary,
    TraceMetadata
)
from backend.app.schemas.wallet import Chain
from backend.app.schemas.graph import FundFlowGraph, GraphNode, GraphEdge
from backend.app.intelligence.models import EntityResolution, VaspAttribution, EntityCandidate, EntityType, ResolutionStatus
from backend.app.schemas.evidence import EvidenceClass, EvidenceType, compute_dossier_sha256
from backend.app.evidence.builder import EvidenceBuilder
from backend.app.reports.pdf_generator import ForensicReportGenerator
from backend.app.reports.action_packet import ActionPacketGenerator

client = TestClient(app)

def create_sample_investigation_response() -> InvestigationResponse:
    root = "0x28c6c06298d514db089934071355e5743bf21d60"
    deposit = "0x742d35cc6634c0532925a3b844bc454e4438f44e"
    
    nodes = [
        GraphNode(
            id=root,
            address=root,
            chain=Chain.ETHEREUM,
            node_type="SUSPECT",
            label="Root Wallet",
            confidence=1.0,
            hop_distance=0,
            is_boundary=False
        ),
        GraphNode(
            id=deposit,
            address=deposit,
            chain=Chain.ETHEREUM,
            node_type="VASP_DEPOSIT",
            label="Binance 14",
            entity_name="Binance",
            entity_type="VASP",
            is_vasp=True,
            confidence=1.0,
            hop_distance=1,
            is_boundary=False
        )
    ]

    edges = [
        GraphEdge(
            id="edge_0x123_0",
            transfer_id="trf_0x123_0",
            tx_hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            source=root,
            target=deposit,
            asset_id="ETH",
            asset_symbol="ETH",
            amount="12.500000000000000000",
            timestamp="2026-03-15T10:30:00Z",
            transfer_type="NATIVE",
            hop=1
        )
    ]

    graph = FundFlowGraph(
        case_id="inv_sample_001",
        suspect_wallet=root,
        chain=Chain.ETHEREUM,
        nodes=nodes,
        edges=edges,
        hop_depth=1,
        total_nodes=2,
        total_edges=1
    )

    trace = TraceMetadata(
        direction="outgoing",
        requested_max_hops=2,
        actual_max_hops=1,
        max_hops_reached=False,
        max_transactions=50,
        transactions_used=1,
        transaction_limit_reached=False,
        boundary_nodes_count=0,
        termination_reason="NATURAL_TERMINATION"
    )

    resolutions = [
        EntityResolution(
            chain="ethereum",
            address=deposit,
            entity_id="binance",
            entity_name="Binance",
            entity_type=EntityType.VASP,
            vasp_status=True,
            source="SEED_REGISTRY",
            source_reference="binance_known_clusters",
            resolution_status=ResolutionStatus.RESOLVED,
            resolved_at=datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
        ),
        EntityResolution(
            chain="ethereum",
            address=root,
            resolution_status=ResolutionStatus.NOT_FOUND,
            vasp_status=False,
            resolved_at=datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
        )
    ]

    vasps = [
        VaspAttribution(
            address=deposit,
            chain="ethereum",
            entity_id="binance",
            entity_name="Binance",
            entity_type=EntityType.VASP,
            vasp_status=True,
            hop_distance=1,
            direction="outgoing",
            path=[root, deposit],
            resolution_status=ResolutionStatus.RESOLVED,
            source="SEED_REGISTRY",
            source_reference="binance_known_clusters",
            relevant_transfer_ids=["trf_0x123_0"]
        )
    ]

    summary = InvestigationSummary(
        nodes=2,
        edges=1,
        transactions=1,
        transfers=1,
        hops=1
    )

    return InvestigationResponse(
        investigation_id="inv_sample_001",
        chain=Chain.ETHEREUM,
        root_address=root,
        status="completed",
        summary=summary,
        graph=graph,
        trace=trace,
        entity_resolutions=resolutions,
        vasp_attributions=vasps,
        created_at=datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
    )

def test_evidence_builder_item_generation():
    inv = create_sample_investigation_response()
    items = EvidenceBuilder.build_evidence_items(inv)
    
    assert len(items) >= 4
    
    classes = [i.evidence_class for i in items]
    assert EvidenceClass.DERIVED in classes or EvidenceClass.OBSERVED in classes
    assert EvidenceClass.OBSERVED in classes
    assert EvidenceClass.RESOLVED in classes
    assert EvidenceClass.UNKNOWN in classes

    # Test exact amount preservation
    transfer_item = next(i for i in items if i.evidence_type == EvidenceType.TRANSFER_OBSERVED.value)
    assert transfer_item.amount == "12.500000000000000000"
    assert transfer_item.tx_hash == "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    assert transfer_item.hop_distance == 1

    # Test resolved entity
    resolved_item = next(i for i in items if i.evidence_type == EvidenceType.ENTITY_RESOLVED.value)
    assert resolved_item.entity_association == "Binance"
    assert resolved_item.source == "SEED_REGISTRY"

    # Test VASP attribution item
    vasp_item = next(i for i in items if i.evidence_type == EvidenceType.VASP_ATTRIBUTED.value)
    assert vasp_item.vasp_association == "Binance"
    assert vasp_item.hop_distance == 1

def test_case_dossier_and_deterministic_hash():
    inv = create_sample_investigation_response()
    dossier1 = EvidenceBuilder.build_case_dossier(inv)
    dossier2 = EvidenceBuilder.build_case_dossier(inv)

    assert dossier1.dossier_id == "dos_inv_sample_001"
    assert len(dossier1.evidence_items) >= 4
    assert dossier1.nodes_count == 2
    assert dossier1.edges_count == 1
    assert len(dossier1.dossier_hash_sha256) == 64
    assert dossier1.dossier_hash_sha256 == dossier2.dossier_hash_sha256

def test_pdf_report_generation():
    inv = create_sample_investigation_response()
    dossier = EvidenceBuilder.build_case_dossier(inv)
    report = ForensicReportGenerator.generate_dossier_report(dossier=dossier)

    assert "report_path" in report
    assert "report_hash" in report
    assert len(report["report_hash"]) == 64
    assert "html_content" in report
    assert "Binance" in report["html_content"]
    assert "OPERATOR VS BENEFICIARY" in report["html_content"]
    assert "12.500000000000000000" in report["html_content"]

def test_action_packet_generation():
    inv = create_sample_investigation_response()
    packet = ActionPacketGenerator.generate_from_investigation(
        investigation=inv,
        investigator="Inspector Jane Doe"
    )

    assert packet.case_id == "inv_sample_001"
    assert packet.attributed_vasp == "Binance"
    assert len(packet.integrity_hash_sha256) == 64
    assert "Inspector Jane Doe" in packet.preservation_notice_draft
    assert "Binance" in packet.preservation_notice_draft
    assert "SECTION 91 CrPC" in packet.preservation_notice_draft

def test_investigations_api_dossier_endpoint():
    inv = create_sample_investigation_response()
    resp = client.post("/api/v1/investigations/dossier", json=inv.model_dump(mode="json"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["dossier_id"] == "dos_inv_sample_001"
    assert len(data["dossier_hash_sha256"]) == 64
    assert len(data["evidence_items"]) >= 4

def test_investigations_api_pdf_endpoint():
    inv = create_sample_investigation_response()
    resp = client.post("/api/v1/investigations/pdf", json=inv.model_dump(mode="json"))
    assert resp.status_code == 200
    data = resp.json()
    assert "report_hash" in data
    assert "html_content" in data
    assert len(data["report_hash"]) == 64

def test_investigations_api_action_packet_endpoint():
    inv = create_sample_investigation_response()
    resp = client.post("/api/v1/investigations/action-packet", json=inv.model_dump(mode="json"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["case_id"] == "inv_sample_001"
    assert data["attributed_vasp"] == "Binance"
    assert len(data["integrity_hash_sha256"]) == 64

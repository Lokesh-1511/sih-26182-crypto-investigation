# backend/app/api/reports.py
from fastapi import APIRouter, Depends, HTTPException
from ..models.database import get_db, Session
from ..models.entities import CaseModel
from ..schemas.wallet import Chain
from ..schemas.snapshot import LawfulActionPacket, InvestigationSnapshot
from ..reports.pdf_generator import ForensicReportGenerator
from ..reports.action_packet import ActionPacketGenerator
from ..evidence.snapshots import SnapshotEngine
from .attribution import _compute_case_attribution
from ..risk.typologies import RiskTypologyEngine
from ..graph.builder import GraphBuilder
from ..blockchain.adapters.fixture_adapter import FixtureBlockchainProvider

router = APIRouter(prefix="/cases", tags=["Reports & Action Packets"])

@router.post("/{case_id}/report")
def export_report(case_id: str, db: Session = Depends(get_db)):
    case_model = db.query(CaseModel).filter_by(id=case_id).first()
    if not case_model:
        raise HTTPException(status_code=404, detail="Case not found")

    attr = _compute_case_attribution(case_id, db)
    prov = FixtureBlockchainProvider()
    chain = Chain(case_model.chain or "ETH")
    suspect_wallet = case_model.suspect_wallet or ""
    transfers = prov.get_case_transfers(case_id, chain, suspect_wallet)
    builder = GraphBuilder()
    graph_data = builder.build_from_transfers(case_id, case_model.suspect_wallet or "", chain, transfers)
    risk_summary = RiskTypologyEngine.analyze_graph(graph_data)

    report_result = ForensicReportGenerator.generate_html_report(
        case_data={
            "id": case_model.id,
            "title": case_model.title,
            "investigator": case_model.investigator,
            "suspect_wallet": case_model.suspect_wallet,
            "chain": case_model.chain,
            "status": case_model.status
        },
        attribution_data=attr.model_dump(),
        risk_data=risk_summary.model_dump()
    )

    return report_result

@router.post("/{case_id}/action-packet", response_model=LawfulActionPacket)
def generate_action_packet(case_id: str, db: Session = Depends(get_db)):
    case_model = db.query(CaseModel).filter_by(id=case_id).first()
    if not case_model:
        raise HTTPException(status_code=404, detail="Case not found")

    attr = _compute_case_attribution(case_id, db)
    if not attr.top_candidate:
        raise HTTPException(status_code=400, detail="Cannot generate action packet without candidate VASP attribution")

    return ActionPacketGenerator.generate_packet(
        case_id=case_id,
        investigator=case_model.investigator,
        suspect_wallet=case_model.suspect_wallet or "N/A",
        chain=case_model.chain or "ETH",
        candidate=attr.top_candidate
    )

@router.get("/{case_id}/snapshot", response_model=InvestigationSnapshot)
def get_investigation_snapshot(case_id: str, db: Session = Depends(get_db)):
    case_model = db.query(CaseModel).filter_by(id=case_id).first()
    if not case_model:
        raise HTTPException(status_code=404, detail="Case not found")

    attr = _compute_case_attribution(case_id, db)
    return SnapshotEngine.create_snapshot(
        case_id=case_id,
        input_wallet=case_model.suspect_wallet or "N/A",
        chain=case_model.chain or "ETH",
        payload_data=attr.model_dump()
    )

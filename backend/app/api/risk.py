# backend/app/api/risk.py
from fastapi import APIRouter, Depends, HTTPException
from ..models.database import get_db, Session
from ..models.entities import CaseModel, TransferModel
from ..schemas.wallet import Chain
from ..schemas.transaction import NormalizedTransfer
from ..schemas.risk import RiskTypologySummary
from ..graph.builder import GraphBuilder
from ..risk.typologies import RiskTypologyEngine
from ..risk.breakpoint import ObfuscationBreakpointDetector
from ..blockchain.adapters.fixture_adapter import FixtureBlockchainProvider

router = APIRouter(prefix="/cases", tags=["Risk"])

@router.get("/{case_id}/risk", response_model=RiskTypologySummary)
def get_case_risk(case_id: str, db: Session = Depends(get_db)):
    case_model = db.query(CaseModel).filter_by(id=case_id).first()
    if not case_model:
        raise HTTPException(status_code=404, detail="Case not found")

    suspect_wallet = case_model.suspect_wallet or "0x71C83e20e8F468a3E282241F8C936f4521487439"
    chain = Chain(case_model.chain or "ETH")

    db_transfers = db.query(TransferModel).all()
    transfers = []
    if db_transfers:
        for tr in db_transfers:
            transfers.append(NormalizedTransfer(
                tx_id=tr.tx_id,
                from_address=tr.from_address,
                to_address=tr.to_address,
                asset=tr.asset,
                amount=tr.amount,
                hop_distance=tr.hop_distance
            ))
    else:
        prov = FixtureBlockchainProvider()
        for tx in prov._cache.values():
            transfers.extend(tx.transfers)

    builder = GraphBuilder()
    graph_data = builder.build_from_transfers(
        case_id=case_id,
        suspect_wallet=suspect_wallet,
        chain=chain,
        transfers=transfers
    )

    return RiskTypologyEngine.analyze_graph(graph_data)

# backend/app/api/attribution.py
from fastapi import APIRouter, Depends, HTTPException
from ..models.database import get_db, Session
from ..models.entities import CaseModel, TransferModel
from ..schemas.wallet import Chain
from ..schemas.transaction import NormalizedTransfer
from ..schemas.attribution import AttributionResponse, VASPAttributionCandidate, CounterfactualResult
from ..graph.builder import GraphBuilder
from ..entities.resolver import EntityResolver
from ..attribution.scorer import VASPAttributionScorer
from ..attribution.counterfactual import CounterfactualEngine
from ..blockchain.adapters.fixture_adapter import FixtureBlockchainProvider

router = APIRouter(prefix="/cases", tags=["Attribution"])

def _compute_case_attribution(case_id: str, db: Session) -> AttributionResponse:
    case_model = db.query(CaseModel).filter_by(id=case_id).first()
    if not case_model:
        raise HTTPException(status_code=404, detail="Case not found")

    suspect_wallet = case_model.suspect_wallet or "0x71C83e20e8F468a3E282241F8C936f4521487439"
    chain = Chain(case_model.chain or "ETH")

    # Ingest transfers from DB or fixture cache
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

    resolver = EntityResolver()
    node_labels = {}
    for t in transfers:
        for addr in (t.from_address, t.to_address):
            res = resolver.resolve(addr)
            if res.get("entity_name"):
                node_labels[addr.lower()] = res

    builder = GraphBuilder()
    graph_data = builder.build_from_transfers(
        case_id=case_id,
        suspect_wallet=suspect_wallet,
        chain=chain,
        transfers=transfers,
        node_labels=node_labels
    )

    scorer = VASPAttributionScorer(resolver=resolver)
    attribution = scorer.evaluate_case(
        case_id=case_id,
        suspect_wallet=suspect_wallet,
        chain=chain,
        graph_data=graph_data
    )

    # Attach counterfactuals to top candidate
    if attribution.top_candidate:
        attribution.top_candidate.counterfactuals = CounterfactualEngine.simulate_ablation(
            attribution.top_candidate
        )

    return attribution

@router.get("/{case_id}/attribution", response_model=AttributionResponse)
def get_case_attribution(case_id: str, db: Session = Depends(get_db)):
    return _compute_case_attribution(case_id, db)

@router.get("/{case_id}/attribution/explanation")
def get_attribution_explanation(case_id: str, db: Session = Depends(get_db)):
    attr = _compute_case_attribution(case_id, db)
    if not attr.top_candidate:
        raise HTTPException(status_code=404, detail="No candidate VASP attributed for this case")
    return {
        "case_id": case_id,
        "candidate": attr.top_candidate.entity_name,
        "confidence_score": attr.top_candidate.confidence_score,
        "confidence_band": attr.top_candidate.confidence_band,
        "operator_attribution": attr.operator_beneficiary.operator_attribution,
        "beneficiary_identity": attr.operator_beneficiary.beneficiary_identity,
        "evidence_factors": attr.top_candidate.factors,
        "supporting_tx_ids": attr.top_candidate.supporting_tx_ids
    }

@router.get("/{case_id}/attribution/counterfactual")
def get_counterfactual_analysis(case_id: str, db: Session = Depends(get_db)):
    attr = _compute_case_attribution(case_id, db)
    if not attr.top_candidate:
        raise HTTPException(status_code=404, detail="No candidate VASP attributed for this case")
    return {
        "case_id": case_id,
        "candidate": attr.top_candidate.entity_name,
        "original_score": attr.top_candidate.confidence_score,
        "counterfactual_simulations": attr.top_candidate.counterfactuals
    }

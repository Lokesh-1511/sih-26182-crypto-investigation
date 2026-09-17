# backend/app/api/graph.py
from fastapi import APIRouter, Depends, HTTPException, Query
from ..models.database import get_db, Session
from ..models.entities import CaseModel, TransferModel
from ..schemas.wallet import Chain
from ..schemas.graph import FundFlowGraph, GraphNode, GraphEdge
from ..schemas.transaction import NormalizedTransfer
from ..graph.builder import GraphBuilder
from ..graph.filters import GraphNoiseFilter
from ..risk.breakpoint import ObfuscationBreakpointDetector
from ..entities.resolver import EntityResolver
from ..blockchain.adapters.fixture_adapter import FixtureBlockchainProvider

router = APIRouter(prefix="/cases", tags=["Graph"])

@router.get("/{case_id}/graph", response_model=FundFlowGraph)
def get_case_graph(
    case_id: str,
    min_amount: float = Query(0.0, description="Minimum transfer amount"),
    hide_dust: bool = Query(True, description="Filter micro-dust transfers"),
    db: Session = Depends(get_db)
):
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
        # Fallback to fixture cache
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

    # Detect breakpoints
    breakpoints = ObfuscationBreakpointDetector.detect_breakpoints(graph_data)
    graph_data.breakpoints = breakpoints

    # Apply noise filters
    filtered_graph = GraphNoiseFilter.apply_filters(
        graph_data,
        min_amount=min_amount,
        hide_dust=hide_dust
    )

    return filtered_graph

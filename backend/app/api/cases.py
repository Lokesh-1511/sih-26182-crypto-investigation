# backend/app/api/cases.py
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from ..models.database import get_db, Session
from ..models.entities import CaseModel, WalletModel
from ..schemas.case import CaseCreate, CaseUpdate, CaseResponse
from ..schemas.wallet import Chain, WalletValidationRequest, WalletValidationResult
from ..blockchain.validation.validator import MultiChainValidator

router = APIRouter(prefix="/cases", tags=["Cases"])

@router.post("", response_model=CaseResponse)
def create_case(case_in: CaseCreate, db: Session = Depends(get_db)):
    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"

    # Validate wallet if supplied
    if case_in.suspect_wallet and case_in.chain:
        val = MultiChainValidator.validate(case_in.suspect_wallet, case_in.chain)
        if not val.valid:
            raise HTTPException(status_code=400, detail=f"Invalid address: {val.validation_message}")

    case_model = CaseModel(
        id=case_id,
        title=case_in.title,
        investigator=case_in.investigator,
        description=case_in.description,
        priority=case_in.priority,
        suspect_wallet=case_in.suspect_wallet,
        chain=case_in.chain.value if case_in.chain else None,
        status="OPEN",
        created_at=datetime.utcnow()
    )
    db.add(case_model)

    if case_in.suspect_wallet and case_in.chain:
        wallet_model = WalletModel(
            case_id=case_id,
            chain=case_in.chain.value,
            address=case_in.suspect_wallet,
            wallet_role="SUSPECT",
            first_seen=datetime.utcnow()
        )
        db.add(wallet_model)

    db.commit()
    db.refresh(case_model)

    return CaseResponse(
        case_id=case_model.id,
        title=case_model.title,
        investigator=case_model.investigator,
        description=case_model.description,
        status=case_model.status,
        priority=case_model.priority,
        suspect_wallet=case_model.suspect_wallet,
        chain=Chain(case_model.chain) if case_model.chain else None,
        created_at=case_model.created_at
    )

@router.get("", response_model=List[CaseResponse])
def list_cases(db: Session = Depends(get_db)):
    cases = db.query(CaseModel).order_by(CaseModel.created_at.desc()).all()
    return [
        CaseResponse(
            case_id=c.id,
            title=c.title,
            investigator=c.investigator,
            description=c.description,
            status=c.status,
            priority=c.priority,
            suspect_wallet=c.suspect_wallet,
            chain=Chain(c.chain) if c.chain else None,
            created_at=c.created_at
        )
        for c in cases
    ]

@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: str, db: Session = Depends(get_db)):
    case_model = db.query(CaseModel).filter_by(id=case_id).first()
    if not case_model:
        raise HTTPException(status_code=404, detail="Case not found")
    return CaseResponse(
        case_id=case_model.id,
        title=case_model.title,
        investigator=case_model.investigator,
        description=case_model.description,
        status=case_model.status,
        priority=case_model.priority,
        suspect_wallet=case_model.suspect_wallet,
        chain=Chain(case_model.chain) if case_model.chain else None,
        created_at=case_model.created_at
    )

@router.post("/validate-address", response_model=WalletValidationResult)
def validate_address(req: WalletValidationRequest):
    return MultiChainValidator.validate(req.address, req.chain)

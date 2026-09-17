# backend/app/models/entities.py
from datetime import datetime
from .database import (
    Base, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, relationship
)

class CaseModel(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    investigator = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="OPEN")
    priority = Column(String, default="MEDIUM")
    suspect_wallet = Column(String, nullable=True)
    chain = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    wallets = relationship("WalletModel", back_populates="case", cascade="all, delete-orphan")
    attributions = relationship("AttributionModel", back_populates="case", cascade="all, delete-orphan")
    risk_events = relationship("RiskEventModel", back_populates="case", cascade="all, delete-orphan")
    snapshots = relationship("SnapshotModel", back_populates="case", cascade="all, delete-orphan")

class WalletModel(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, ForeignKey("cases.id"), index=True)
    chain = Column(String, nullable=False)
    address = Column(String, index=True, nullable=False)
    wallet_role = Column(String, default="SUSPECT")
    label = Column(String, nullable=True)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)

    case = relationship("CaseModel", back_populates="wallets")

class TransactionModel(Base):
    __tablename__ = "transactions"

    tx_id = Column(String, primary_key=True, index=True)
    chain = Column(String, nullable=False)
    block_number = Column(Integer, nullable=True)
    timestamp = Column(DateTime, nullable=False)
    fee = Column(Float, default=0.0)
    status = Column(String, default="SUCCESS")
    raw_reference = Column(Text, nullable=True)
    source = Column(String, default="CONTROLLED_FIXTURE")
    retrieved_at = Column(DateTime, default=datetime.utcnow)

    transfers = relationship("TransferModel", back_populates="transaction", cascade="all, delete-orphan")

class TransferModel(Base):
    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tx_id = Column(String, ForeignKey("transactions.tx_id"), index=True)
    from_address = Column(String, index=True, nullable=False)
    to_address = Column(String, index=True, nullable=False)
    asset = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    hop_distance = Column(Integer, default=0)

    transaction = relationship("TransactionModel", back_populates="transfers")

class EntityLabelModel(Base):
    __tablename__ = "entity_labels"

    address = Column(String, primary_key=True, index=True)
    chain = Column(String, nullable=False)
    entity_name = Column(String, index=True, nullable=False)
    entity_type = Column(String, nullable=False)
    confidence = Column(Float, default=1.0)
    label_source = Column(String, default="CONTROLLED_DEMO")
    notes = Column(Text, nullable=True)

class AttributionModel(Base):
    __tablename__ = "attributions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, ForeignKey("cases.id"), index=True)
    candidate_vasp = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False)
    confidence_band = Column(String, nullable=False)
    operator_attribution = Column(String, default="VASP-Controlled Infrastructure")
    beneficiary_identity = Column(String, default="NOT ESTABLISHED")
    evidence_breakdown_json = Column(Text, nullable=False)
    model_version = Column(String, default="v1.0.0")
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="attributions")

class RiskEventModel(Base):
    __tablename__ = "risk_events"

    id = Column(String, primary_key=True, index=True)
    case_id = Column(String, ForeignKey("cases.id"), index=True)
    typology_code = Column(String, nullable=False)
    typology_name = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    node_address = Column(String, nullable=False)
    explanation = Column(Text, nullable=False)
    evidence_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="risk_events")

class SnapshotModel(Base):
    __tablename__ = "analysis_snapshots"

    id = Column(String, primary_key=True, index=True)
    case_id = Column(String, ForeignKey("cases.id"), index=True)
    snapshot_hash = Column(String, nullable=False)
    payload_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="snapshots")

class AuditLogModel(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    object_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_hash = Column(String, nullable=False)
    details = Column(Text, nullable=True)

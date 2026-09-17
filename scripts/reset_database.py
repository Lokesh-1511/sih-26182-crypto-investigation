# scripts/reset_database.py
import sys
import os

# Add repo root to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.models.database import engine, Base
from backend.app.models.entities import (
    CaseModel,
    WalletModel,
    TransactionModel,
    TransferModel,
    EntityLabelModel,
    AttributionModel,
    RiskEventModel,
    SnapshotModel,
    AuditLogModel
)

def reset_db():
    print("Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating all database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database successfully initialized!")

if __name__ == "__main__":
    reset_db()

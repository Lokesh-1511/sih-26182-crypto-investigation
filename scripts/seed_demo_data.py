# scripts/seed_demo_data.py
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.models.database import SessionLocal, Base, engine
from backend.app.models.entities import (
    CaseModel,
    WalletModel,
    TransactionModel,
    TransferModel,
    EntityLabelModel
)

def seed_demo():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    kb_dir = os.path.join(base_dir, "data", "knowledge_base")
    demo_dir = os.path.join(base_dir, "data", "demo")

    print("Seeding Entity Labels from Knowledge Base...")
    # Load deposit wallets & hot wallets into EntityLabelModel
    for fname in ["deposit_wallets.json", "hot_wallets.json", "bridges.json", "mixers.json"]:
        fpath = os.path.join(kb_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                entries = json.load(f)
                for item in entries:
                    addr = item.get("address")
                    if addr:
                        existing = db.query(EntityLabelModel).filter_by(address=addr).first()
                        if not existing:
                            lbl = EntityLabelModel(
                                address=addr,
                                chain=item.get("chain", "ETH"),
                                entity_name=item.get("entity_name", "UNKNOWN"),
                                entity_type=item.get("entity_type", "VASP"),
                                confidence=float(item.get("confidence", 1.0)),
                                label_source=item.get("label_source", "CONTROLLED_DEMO"),
                                notes=item.get("notes")
                            )
                            db.add(lbl)
    db.commit()

    print("Seeding Demo Cases...")
    cases_dir = os.path.join(demo_dir, "cases")
    if os.path.exists(cases_dir):
        for fname in os.listdir(cases_dir):
            if fname.endswith(".json"):
                with open(os.path.join(cases_dir, fname), "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                    cid = cdata.get("case_id")
                    if cid and not db.query(CaseModel).filter_by(id=cid).first():
                        case_obj = CaseModel(
                            id=cid,
                            title=cdata.get("title", "Demo Case"),
                            investigator=cdata.get("investigator", "Investigator"),
                            description=cdata.get("description"),
                            status="OPEN",
                            priority=cdata.get("priority", "MEDIUM"),
                            suspect_wallet=cdata.get("suspect_wallet"),
                            chain=cdata.get("chain", "ETH"),
                            created_at=datetime.utcnow()
                        )
                        db.add(case_obj)
    db.commit()

    print("Seeding Case B Normalized Transactions...")
    tx_file = os.path.join(demo_dir, "transactions", "case_b_transactions.json")
    if os.path.exists(tx_file):
        with open(tx_file, "r", encoding="utf-8") as f:
            tx_records = json.load(f)
            for tx in tx_records:
                tx_id = tx.get("tx_id")
                if not db.query(TransactionModel).filter_by(tx_id=tx_id).first():
                    tx_model = TransactionModel(
                        tx_id=tx_id,
                        chain=tx.get("chain", "ETH"),
                        block_number=tx.get("block_number"),
                        timestamp=datetime.fromisoformat(tx["timestamp"].replace("Z", "+00:00")),
                        fee=float(tx.get("fee", 0.0)),
                        status="SUCCESS",
                        raw_reference=str(tx),
                        source="CONTROLLED_FIXTURE",
                        retrieved_at=datetime.utcnow()
                    )
                    db.add(tx_model)
                    for tr in tx.get("transfers", []):
                        tr_model = TransferModel(
                            tx_id=tx_id,
                            from_address=tr.get("from_address"),
                            to_address=tr.get("to_address"),
                            asset=tr.get("asset", "ETH"),
                            amount=float(tr.get("amount", 0.0)),
                            hop_distance=int(tr.get("hop_distance", 0))
                        )
                        db.add(tr_model)
    db.commit()
    db.close()
    print("Demo data seeding completed successfully!")

if __name__ == "__main__":
    seed_demo()

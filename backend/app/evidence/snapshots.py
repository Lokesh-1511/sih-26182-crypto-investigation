# backend/app/evidence/snapshots.py
import json
import hashlib
from datetime import datetime
from typing import Dict, Any
from ..schemas.snapshot import InvestigationSnapshot

class SnapshotEngine:
    """
    Creates tamper-evident cryptographic snapshots of investigation cases.
    Computes SHA-256 integrity digests for legal admissibility.
    """

    @classmethod
    def create_snapshot(
        cls,
        case_id: str,
        input_wallet: str,
        chain: str,
        payload_data: Dict[str, Any]
    ) -> InvestigationSnapshot:
        serialized = json.dumps(payload_data, sort_keys=True, default=str)
        sha256_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        return InvestigationSnapshot(
            snapshot_id=f"snap_{case_id}_{int(datetime.utcnow().timestamp())}",
            case_id=case_id,
            input_wallet=input_wallet,
            chain=chain,
            created_at=datetime.utcnow(),
            algorithm_version="v1.0.0",
            kb_version="v2026.1",
            integrity_hash_sha256=sha256_hash,
            snapshot_payload=payload_data
        )

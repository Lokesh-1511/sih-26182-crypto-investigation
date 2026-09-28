# backend/app/blockchain/normalization/base.py
import hashlib
import json
from abc import ABC, abstractmethod
from typing import Dict, Any
from ..models.enums import Chain
from ..models.transaction import NormalizedTransaction

class BaseNormalizer(ABC):
    """Abstract base class for chain-specific raw response normalizers."""

    @property
    @abstractmethod
    def supported_chain(self) -> Chain:
        """The chain handled by this normalizer."""
        pass

    @abstractmethod
    def normalize_transaction(
        self,
        raw_tx: Dict[str, Any],
        provider: str = "PROVIDER"
    ) -> NormalizedTransaction:
        """Parse provider-specific raw payload into canonical NormalizedTransaction."""
        pass

    @staticmethod
    def calculate_payload_hash(raw_data: Any) -> str:
        """Calculate SHA-256 integrity hash of raw payload."""
        if isinstance(raw_data, (dict, list)):
            canonical_json = json.dumps(raw_data, sort_keys=True, default=str)
            return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
        elif isinstance(raw_data, str):
            return hashlib.sha256(raw_data.encode("utf-8")).hexdigest()
        return hashlib.sha256(str(raw_data).encode("utf-8")).hexdigest()

# backend/app/blockchain/validation/base.py
from abc import ABC, abstractmethod
from ..models.enums import Chain
from ..models.provider import AddressValidation

class BaseAddressValidator(ABC):
    """Abstract base validator for a specific blockchain family."""

    @abstractmethod
    def validate(self, address: str) -> AddressValidation:
        """Validate cryptocurrency address structure and cryptographic checksum."""
        pass

    @property
    @abstractmethod
    def supported_chain(self) -> Chain:
        """The primary chain supported by this validator."""
        pass

# backend/app/blockchain/validation/tron.py
import hashlib
from typing import Optional
from .base import BaseAddressValidator
from ..models.enums import Chain
from ..models.provider import AddressValidation

# Base58 Alphabet
B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
B58_MAP = {c: i for i, c in enumerate(B58_ALPHABET)}


def _b58decode_check_tron(addr: str) -> Optional[bytes]:
    """Decode Tron Base58Check address and verify double SHA-256 checksum."""
    if not addr or any(c not in B58_MAP for c in addr):
        return None

    num = 0
    for c in addr:
        num = num * 58 + B58_MAP[c]

    raw = []
    while num > 0:
        raw.append(num & 0xFF)
        num >>= 8
    raw.reverse()

    leading_ones = len(addr) - len(addr.lstrip('1'))
    decoded = bytes([0] * leading_ones + raw)

    if len(decoded) != 25:
        return None

    payload, checksum = decoded[:-4], decoded[-4:]
    expected_checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    if checksum != expected_checksum:
        return None

    return payload


class TronAddressValidator(BaseAddressValidator):
    """Validator for TRON Base58Check addresses (starts with 'T', 0x41 network prefix)."""

    @property
    def supported_chain(self) -> Chain:
        return Chain.TRON

    def validate(self, address: str) -> AddressValidation:
        if not isinstance(address, str):
            return AddressValidation(
                valid=False,
                checksum_valid=False,
                normalized_address="",
                chain=Chain.TRON,
                reason="Address must be a string"
            )

        addr = address.strip()

        if not addr.startswith("T"):
            return AddressValidation(
                valid=False,
                checksum_valid=False,
                normalized_address=addr,
                chain=Chain.TRON,
                reason="Tron address must begin with 'T'"
            )

        if len(addr) != 34:
            return AddressValidation(
                valid=False,
                checksum_valid=False,
                normalized_address=addr,
                chain=Chain.TRON,
                reason=f"Invalid Tron address length: expected 34 characters, got {len(addr)}"
            )

        payload = _b58decode_check_tron(addr)
        if payload is None:
            return AddressValidation(
                valid=False,
                checksum_valid=False,
                normalized_address=addr,
                chain=Chain.TRON,
                reason="Invalid Tron Base58Check checksum or character encoding"
            )

        if payload[0] != 0x41:
            return AddressValidation(
                valid=False,
                checksum_valid=False,
                normalized_address=addr,
                chain=Chain.TRON,
                reason=f"Invalid Tron prefix byte: expected 0x41, got 0x{payload[0]:02x}"
            )

        return AddressValidation(
            valid=True,
            checksum_valid=True,
            normalized_address=addr,
            chain=Chain.TRON,
            reason="Valid Tron Base58Check address",
            format_type="BASE58CHECK_TRON"
        )

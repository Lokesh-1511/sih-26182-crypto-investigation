# backend/app/blockchain/validation/bitcoin.py
import hashlib
import re
from typing import Optional, Tuple
from .base import BaseAddressValidator
from ..models.enums import Chain
from ..models.provider import AddressValidation

# Base58 Alphabet
B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
B58_MAP = {c: i for i, c in enumerate(B58_ALPHABET)}

# Bech32 / Bech32m character set and values
BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
BECH32_MAP = {c: i for i, c in enumerate(BECH32_CHARSET)}
BECH32_CONST = 1
BECH32M_CONST = 0x2bc830a3


def _b58decode_check(addr: str) -> Optional[bytes]:
    """Decode Base58Check string and verify the 4-byte double SHA-256 checksum."""
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

    if len(decoded) < 4:
        return None

    payload, checksum = decoded[:-4], decoded[-4:]
    expected_checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    if checksum != expected_checksum:
        return None

    return payload


def _bech32_polymod(values: list[int]) -> int:
    GEN = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for v in values:
        b = chk >> 25
        chk = ((chk & 0x1ffffff) << 5) ^ v
        for i in range(5):
            chk ^= GEN[i] if ((b >> i) & 1) else 0
    return chk


def _bech32_hrp_expand(hrp: str) -> list[int]:
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def _bech32_verify_checksum(hrp: str, data: list[int]) -> Optional[str]:
    poly = _bech32_polymod(_bech32_hrp_expand(hrp) + data)
    if poly == BECH32_CONST:
        return "BECH32_SEGWIT"
    elif poly == BECH32M_CONST:
        return "BECH32M_TAPROOT"
    return None


def _decode_bech32(addr: str) -> Tuple[Optional[str], Optional[list[int]], Optional[str]]:
    if ((addr.lower() != addr) and (addr.upper() != addr)) or len(addr) < 8 or len(addr) > 90:
        return None, None, None

    addr = addr.lower()
    pos = addr.rfind("1")
    if pos < 1 or pos + 7 > len(addr):
        return None, None, None

    hrp = addr[:pos]
    data_str = addr[pos + 1:]
    if any(c not in BECH32_MAP for c in data_str):
        return None, None, None

    data = [BECH32_MAP[c] for c in data_str]
    spec = _bech32_verify_checksum(hrp, data)
    if spec is None:
        return None, None, None

    return hrp, data[:-6], spec


class BitcoinAddressValidator(BaseAddressValidator):
    """Validator for Bitcoin addresses (Legacy P2PKH, Nested P2SH, Native SegWit, and Taproot)."""

    @property
    def supported_chain(self) -> Chain:
        return Chain.BITCOIN

    def validate(self, address: str) -> AddressValidation:
        if not isinstance(address, str):
            return AddressValidation(
                valid=False,
                checksum_valid=False,
                normalized_address="",
                chain=Chain.BITCOIN,
                reason="Address must be a string"
            )

        addr = address.strip()

        # 1. Native SegWit (Bech32) / Taproot (Bech32m): starts with bc1
        if addr.lower().startswith("bc1"):
            hrp, data, spec = _decode_bech32(addr)
            if hrp != "bc" or not data:
                return AddressValidation(
                    valid=False,
                    checksum_valid=False,
                    normalized_address=addr,
                    chain=Chain.BITCOIN,
                    reason="Invalid Bitcoin Bech32/Bech32m Segwit/Taproot address or checksum mismatch"
                )

            witness_version = data[0]
            if witness_version == 0 and spec == "BECH32_SEGWIT":
                return AddressValidation(
                    valid=True,
                    checksum_valid=True,
                    normalized_address=addr.lower(),
                    chain=Chain.BITCOIN,
                    reason="Valid Bitcoin BECH32_SEGWIT address",
                    format_type="BECH32_SEGWIT"
                )
            elif witness_version == 1 and spec == "BECH32M_TAPROOT":
                return AddressValidation(
                    valid=True,
                    checksum_valid=True,
                    normalized_address=addr.lower(),
                    chain=Chain.BITCOIN,
                    reason="Valid Bitcoin BECH32M_TAPROOT address",
                    format_type="BECH32M_TAPROOT"
                )
            elif spec is not None:
                return AddressValidation(
                    valid=True,
                    checksum_valid=True,
                    normalized_address=addr.lower(),
                    chain=Chain.BITCOIN,
                    reason=f"Valid Bitcoin {spec} address",
                    format_type=spec
                )
            else:
                return AddressValidation(
                    valid=False,
                    checksum_valid=False,
                    normalized_address=addr,
                    chain=Chain.BITCOIN,
                    reason="Invalid Bitcoin Bech32/Bech32m witness program"
                )

        # 2. Legacy P2PKH ('1') and P2SH ('3') Base58Check addresses
        if addr.startswith("1") or addr.startswith("3"):
            if not (26 <= len(addr) <= 35):
                return AddressValidation(
                    valid=False,
                    checksum_valid=False,
                    normalized_address=addr,
                    chain=Chain.BITCOIN,
                    reason="Invalid Bitcoin legacy address length (must be 26-35 characters)"
                )

            decoded = _b58decode_check(addr)
            if decoded is None:
                return AddressValidation(
                    valid=False,
                    checksum_valid=False,
                    normalized_address=addr,
                    chain=Chain.BITCOIN,
                    reason="Invalid Bitcoin Base58Check address or checksum mismatch"
                )

            version_byte = decoded[0]
            if version_byte == 0x00:
                fmt = "P2PKH_LEGACY"
            elif version_byte == 0x05:
                fmt = "P2SH_SEGWIT"
            else:
                fmt = "BASE58_OTHER"

            return AddressValidation(
                valid=True,
                checksum_valid=True,
                normalized_address=addr,
                chain=Chain.BITCOIN,
                reason=f"Valid Bitcoin {fmt} address",
                format_type=fmt
            )

        return AddressValidation(
            valid=False,
            checksum_valid=False,
            normalized_address=addr,
            chain=Chain.BITCOIN,
            reason="Bitcoin address must begin with '1', '3', or 'bc1'"
        )

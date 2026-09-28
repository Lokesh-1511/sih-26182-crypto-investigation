# backend/app/blockchain/validation/evm.py
import re
from typing import Optional
from .base import BaseAddressValidator
from ..models.enums import Chain
from ..models.provider import AddressValidation


def _keccak_256(data: bytes) -> bytes:
    """
    Standard Keccak-256 implementation (padding 0x01 ... 0x80, rate 1088 bits).
    Complies with Ethereum EIP-55 checksum specification.
    """
    RC = [
        0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
        0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
        0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
        0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
        0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
        0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008
    ]
    ROT = [
        [0,  36,  3, 41, 18],
        [1,  44, 10, 45,  2],
        [62,  6, 43, 15, 61],
        [28, 55, 25, 21, 56],
        [27, 20, 39,  8, 14]
    ]

    rate_bytes = 136  # (1600 - 512) // 8
    padded = bytearray(data)
    padded.append(0x01)
    while len(padded) % rate_bytes != (rate_bytes - 1):
        padded.append(0x00)
    padded.append(0x80)

    state = [[0] * 5 for _ in range(5)]

    def _rotl64(x: int, n: int) -> int:
        return ((x << (n % 64)) | (x >> ((64 - (n % 64)) % 64))) & 0xFFFFFFFFFFFFFFFF

    for block_idx in range(0, len(padded), rate_bytes):
        block = padded[block_idx:block_idx + rate_bytes]
        for i in range(rate_bytes // 8):
            val = int.from_bytes(block[i * 8:(i + 1) * 8], byteorder="little")
            x, y = i % 5, i // 5
            state[x][y] ^= val

        for round_idx in range(24):
            C = [state[x][0] ^ state[x][1] ^ state[x][2] ^ state[x][3] ^ state[x][4] for x in range(5)]
            D = [C[(x + 4) % 5] ^ _rotl64(C[(x + 1) % 5], 1) for x in range(5)]
            for x in range(5):
                for y in range(5):
                    state[x][y] ^= D[x]

            B = [[0] * 5 for _ in range(5)]
            for x in range(5):
                for y in range(5):
                    B[y][(2 * x + 3 * y) % 5] = _rotl64(state[x][y], ROT[x][y])

            for x in range(5):
                for y in range(5):
                    state[x][y] = (B[x][y] ^ ((~B[(x + 1) % 5][y]) & B[(x + 2) % 5][y])) & 0xFFFFFFFFFFFFFFFF

            state[0][0] ^= RC[round_idx]

    out = bytearray()
    for i in range(4):
        x, y = i % 5, i // 5
        out.extend(state[x][y].to_bytes(8, byteorder="little"))
    return bytes(out)


def to_checksum_address(address: str) -> str:
    """Convert an EVM address to its canonical EIP-55 checksummed representation."""
    addr_clean = address.lower().replace("0x", "")
    h = _keccak_256(addr_clean.encode("ascii")).hex()
    checksummed = ["0x"]
    for char, hash_char in zip(addr_clean, h):
        if int(hash_char, 16) >= 8:
            checksummed.append(char.upper())
        else:
            checksummed.append(char.lower())
    return "".join(checksummed)


class EVMAddressValidator(BaseAddressValidator):
    """Validator for Ethereum and EVM-compatible chains (BNB, Polygon, Arbitrum, etc.)."""

    def __init__(self, chain: Chain = Chain.ETHEREUM):
        self._chain = chain

    @property
    def supported_chain(self) -> Chain:
        return self._chain

    def validate(self, address: str) -> AddressValidation:
        if not isinstance(address, str):
            return AddressValidation(
                valid=False,
                checksum_valid=False,
                normalized_address="",
                chain=self._chain,
                reason="Address must be a string"
            )

        addr = address.strip()
        if not re.match(r"^0x[a-fA-F0-9]{40}$", addr):
            return AddressValidation(
                valid=False,
                checksum_valid=False,
                normalized_address=addr,
                chain=self._chain,
                reason="Invalid EVM address format: must start with 0x and contain exactly 40 hex characters"
            )

        hex_body = addr[2:]
        is_mixed_case = any(c.isupper() for c in hex_body) and any(c.islower() for c in hex_body)
        expected_checksum = to_checksum_address(addr)

        if is_mixed_case:
            if addr == expected_checksum:
                return AddressValidation(
                    valid=True,
                    checksum_valid=True,
                    normalized_address=expected_checksum,
                    chain=self._chain,
                    reason="Valid EIP-55 Checksummed EVM Address",
                    format_type="EIP-55"
                )
            else:
                return AddressValidation(
                    valid=True,
                    checksum_valid=False,
                    normalized_address=expected_checksum,
                    chain=self._chain,
                    reason=f"Valid Hex EVM Address (EIP-55 checksum mismatch, expected {expected_checksum})",
                    format_type="HEX_MIXED_INVALID_CHECKSUM"
                )

        return AddressValidation(
            valid=True,
            checksum_valid=None,
            normalized_address=expected_checksum,
            chain=self._chain,
            reason="Valid Raw Hex EVM Address",
            format_type="HEX_RAW"
        )

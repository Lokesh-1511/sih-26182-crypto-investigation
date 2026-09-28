# backend/app/blockchain/models/enums.py
from enum import Enum

class Chain(str, Enum):
    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum"
    BNB = "bnb"
    POLYGON = "polygon"
    TRON = "tron"

    # Backward compatibility aliases
    BTC = "bitcoin"
    ETH = "ethereum"
    TRX = "tron"
    SOL = "solana"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val_lower = value.strip().lower()
            mapping = {
                "btc": cls.BITCOIN,
                "bitcoin": cls.BITCOIN,
                "eth": cls.ETHEREUM,
                "ethereum": cls.ETHEREUM,
                "bnb": cls.BNB,
                "binance": cls.BNB,
                "bsc": cls.BNB,
                "polygon": cls.POLYGON,
                "matic": cls.POLYGON,
                "trx": cls.TRON,
                "tron": cls.TRON,
                "sol": "solana",
                "solana": "solana"
            }
            if val_lower in mapping:
                return mapping[val_lower]
        return super()._missing_(value)


class TransferDirection(str, Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"
    ANY = "any"


class TransactionStatus(str, Enum):
    CONFIRMED = "confirmed"
    FAILED = "failed"
    PENDING = "pending"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val_lower = value.strip().lower()
            if val_lower in ("success", "confirmed", "1", "true", "ok"):
                return cls.CONFIRMED
            elif val_lower in ("failed", "failure", "error", "0", "false"):
                return cls.FAILED
            elif val_lower in ("pending", "queued", "mempool"):
                return cls.PENDING
        return cls.UNKNOWN


class TransactionType(str, Enum):
    NATIVE_TRANSFER = "native_transfer"
    TOKEN_TRANSFER = "token_transfer"
    CONTRACT_CALL = "contract_call"
    UTXO_TRANSACTION = "utxo_transaction"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class AssetType(str, Enum):
    NATIVE = "native"
    ERC20 = "erc20"
    BEP20 = "bep20"
    TRC20 = "trc20"
    OMNI = "omni"
    UNKNOWN = "unknown"


class TransferType(str, Enum):
    NATIVE = "native"
    TOKEN = "token"
    INTERNAL = "internal"
    UTXO_OUTPUT = "utxo_output"

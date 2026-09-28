# backend/app/blockchain/normalization/normalizer.py
from typing import Dict, Any
from ..models.enums import Chain
from ..models.transaction import NormalizedTransaction
from .bitcoin import BitcoinNormalizer
from .evm import EVMNormalizer
from .tron import TronNormalizer

class TransactionNormalizer:
    """
    Multi-chain normalizer orchestrator.
    Normalizes multi-chain blockchain records (UTXO, EVM Account, TRC20)
    into standard NormalizedTransaction and NormalizedTransfer structures.
    """

    _btc_normalizer = BitcoinNormalizer()
    _evm_normalizer = EVMNormalizer(Chain.ETHEREUM)
    _bnb_normalizer = EVMNormalizer(Chain.BNB)
    _polygon_normalizer = EVMNormalizer(Chain.POLYGON)
    _tron_normalizer = TronNormalizer()

    @classmethod
    def normalize_transaction(
        cls,
        tx_data: Dict[str, Any],
        chain: Chain = Chain.ETHEREUM,
        provider: str = "PROVIDER"
    ) -> NormalizedTransaction:
        if not isinstance(chain, Chain):
            try:
                chain = Chain(chain)
            except ValueError:
                chain = Chain.ETHEREUM

        if chain in (Chain.BITCOIN, Chain.BTC):
            return cls._btc_normalizer.normalize_transaction(tx_data, provider=provider)
        elif chain in (Chain.TRON, Chain.TRX):
            return cls._tron_normalizer.normalize_transaction(tx_data, provider=provider)
        elif chain == Chain.BNB:
            return cls._bnb_normalizer.normalize_transaction(tx_data, provider=provider)
        elif chain == Chain.POLYGON:
            return cls._polygon_normalizer.normalize_transaction(tx_data, provider=provider)
        else:
            return cls._evm_normalizer.normalize_transaction(tx_data, provider=provider)

    @classmethod
    def normalize_account_transfer(
        cls,
        tx_data: Dict[str, Any],
        chain: Chain = Chain.ETHEREUM
    ) -> NormalizedTransaction:
        """Compatibility helper for EVM and Tron account-based transactions."""
        return cls.normalize_transaction(tx_data, chain=chain, provider="NORMALIZED_ACCOUNT")

    @classmethod
    def normalize_utxo_transaction(
        cls,
        tx_data: Dict[str, Any],
        chain: Chain = Chain.BITCOIN
    ) -> NormalizedTransaction:
        """Compatibility helper for Bitcoin UTXO transactions with inputs and outputs."""
        return cls.normalize_transaction(tx_data, chain=chain, provider="NORMALIZED_UTXO")

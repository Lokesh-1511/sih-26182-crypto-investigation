# backend/app/blockchain/validation/validator.py
from typing import Tuple, Optional
from ..models.enums import Chain
from ..models.provider import AddressValidation
from .evm import EVMAddressValidator
from .bitcoin import BitcoinAddressValidator
from .tron import TronAddressValidator

class MultiChainValidator:
    """
    Multi-chain cryptographic address validator orchestrator.
    Dispatches validation requests to chain-specific validators.
    """

    _evm_validator = EVMAddressValidator(Chain.ETHEREUM)
    _bnb_validator = EVMAddressValidator(Chain.BNB)
    _polygon_validator = EVMAddressValidator(Chain.POLYGON)
    _btc_validator = BitcoinAddressValidator()
    _tron_validator = TronAddressValidator()

    @classmethod
    def validate_ethereum(cls, address: str) -> Tuple[bool, str, Optional[str]]:
        res = cls._evm_validator.validate(address)
        return res.valid, res.reason or "", res.format_type

    @classmethod
    def validate_bitcoin(cls, address: str) -> Tuple[bool, str, Optional[str]]:
        res = cls._btc_validator.validate(address)
        return res.valid, res.reason or "", res.format_type

    @classmethod
    def validate_tron(cls, address: str) -> Tuple[bool, str, Optional[str]]:
        res = cls._tron_validator.validate(address)
        return res.valid, res.reason or "", res.format_type

    @classmethod
    def validate(cls, address: str, chain: Chain) -> AddressValidation:
        if not isinstance(chain, Chain):
            try:
                chain = Chain(chain)
            except ValueError:
                return AddressValidation(
                    valid=False,
                    normalized_address=address,
                    chain=Chain.ETHEREUM,
                    reason=f"Unsupported blockchain network: {chain}"
                )

        if chain in (Chain.ETHEREUM, Chain.ETH):
            return cls._evm_validator.validate(address)
        elif chain in (Chain.BNB, Chain.POLYGON):
            validator = cls._bnb_validator if chain == Chain.BNB else cls._polygon_validator
            return validator.validate(address)
        elif chain in (Chain.BITCOIN, Chain.BTC):
            return cls._btc_validator.validate(address)
        elif chain in (Chain.TRON, Chain.TRX):
            return cls._tron_validator.validate(address)
        else:
            return AddressValidation(
                valid=False,
                normalized_address=address,
                chain=chain,
                reason=f"Validator not configured for chain: {chain}"
            )

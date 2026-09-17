# tests/unit/test_validation.py
import pytest
from backend.app.blockchain.validation.validator import MultiChainValidator
from backend.app.schemas.wallet import Chain

def test_ethereum_address_validation():
    # Valid EIP-55
    res1 = MultiChainValidator.validate("0x71C83e20e8F468a3E282241F8C936f4521487439", Chain.ETH)
    assert res1.valid is True
    assert res1.chain == Chain.ETH

    # Valid lowercase
    res2 = MultiChainValidator.validate("0xd8da6bf26964af9d7eed9e03e53415d37aa96045", Chain.ETH)
    assert res2.valid is True

    # Malformed length
    res3 = MultiChainValidator.validate("0x1234", Chain.ETH)
    assert res3.valid is False

    # Invalid non-hex chars
    res4 = MultiChainValidator.validate("0xZZZZ3e20e8F468a3E282241F8C936f4521487439", Chain.ETH)
    assert res4.valid is False

def test_bitcoin_address_validation():
    # Legacy P2PKH (1...)
    res1 = MultiChainValidator.validate("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", Chain.BTC)
    assert res1.valid is True
    assert res1.format_type == "P2PKH_LEGACY"

    # P2SH (3...)
    res2 = MultiChainValidator.validate("3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy", Chain.BTC)
    assert res2.valid is True
    assert res2.format_type == "P2SH_SEGWIT"

    # Bech32 SegWit (bc1q...)
    res3 = MultiChainValidator.validate("bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq", Chain.BTC)
    assert res3.valid is True
    assert res3.format_type == "BECH32_SEGWIT"

    # Malformed legacy (contains invalid Base58 character '0')
    res4 = MultiChainValidator.validate("101zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", Chain.BTC)
    assert res4.valid is False

def test_tron_address_validation():
    # Valid Tron Base58Check
    res1 = MultiChainValidator.validate("TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t", Chain.TRX)
    assert res1.valid is True
    assert res1.format_type == "BASE58CHECK_TRON"

    # Invalid start char
    res2 = MultiChainValidator.validate("XR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t", Chain.TRX)
    assert res2.valid is False

    # Invalid length
    res3 = MultiChainValidator.validate("TR7NHqjeKQxGTCi8q8", Chain.TRX)
    assert res3.valid is False

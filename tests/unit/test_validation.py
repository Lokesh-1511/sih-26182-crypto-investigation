# tests/unit/test_validation.py
import pytest
from backend.app.blockchain.validation.validator import MultiChainValidator
from backend.app.blockchain.validation.evm import to_checksum_address
from backend.app.blockchain.models.enums import Chain

def test_ethereum_address_validation():
    # Valid EIP-55 Checksum
    valid_eip55 = "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
    res1 = MultiChainValidator.validate(valid_eip55, Chain.ETHEREUM)
    assert res1.valid is True
    assert res1.checksum_valid is True
    assert res1.format_type == "EIP-55"
    assert res1.normalized_address == valid_eip55

    # Valid lowercase (converted to normalized checksum, checksum_valid is None/not required)
    raw_lower = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"
    res2 = MultiChainValidator.validate(raw_lower, Chain.ETH)
    assert res2.valid is True
    assert res2.normalized_address == to_checksum_address(raw_lower)

    # Valid address with non-matching mixed casing: valid=True, checksum_valid=False
    mixed_invalid = "0x71C83e20e8F468a3E282241F8C936f4521487439"
    res_mixed = MultiChainValidator.validate(mixed_invalid, Chain.ETH)
    assert res_mixed.valid is True
    assert res_mixed.checksum_valid is False
    assert res_mixed.normalized_address == to_checksum_address(mixed_invalid)
    assert res_mixed.format_type == "HEX_MIXED_INVALID_CHECKSUM"

    # Invalid length
    res3 = MultiChainValidator.validate("0x1234", Chain.ETH)
    assert res3.valid is False
    assert res3.checksum_valid is False

    # Invalid non-hex chars
    res4 = MultiChainValidator.validate("0xZZZZ3e20e8F468a3E282241F8C936f4521487439", Chain.ETH)
    assert res4.valid is False
    assert res4.checksum_valid is False

    # BNB and Polygon validation
    res_bnb = MultiChainValidator.validate(valid_eip55, Chain.BNB)
    assert res_bnb.valid is True
    res_poly = MultiChainValidator.validate(valid_eip55, Chain.POLYGON)
    assert res_poly.valid is True


def test_bitcoin_address_validation():
    # Legacy P2PKH (1...)
    res1 = MultiChainValidator.validate("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", Chain.BITCOIN)
    assert res1.valid is True
    assert res1.checksum_valid is True
    assert res1.format_type == "P2PKH_LEGACY"

    # P2SH (3...)
    res2 = MultiChainValidator.validate("3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy", Chain.BTC)
    assert res2.valid is True
    assert res2.checksum_valid is True
    assert res2.format_type == "P2SH_SEGWIT"

    # Bech32 SegWit v0 (bc1q...)
    res3 = MultiChainValidator.validate("bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq", Chain.BTC)
    assert res3.valid is True
    assert res3.checksum_valid is True
    assert res3.format_type == "BECH32_SEGWIT"

    # Bech32m Taproot v1 (bc1p...)
    res_taproot = MultiChainValidator.validate("bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0", Chain.BITCOIN)
    assert res_taproot.valid is True
    assert res_taproot.checksum_valid is True
    assert res_taproot.format_type == "BECH32M_TAPROOT"

    # Malformed legacy (contains invalid Base58 character '0')
    res4 = MultiChainValidator.validate("101zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", Chain.BTC)
    assert res4.valid is False
    assert res4.checksum_valid is False

    # Base58Check checksum mismatch (last char altered)
    res5 = MultiChainValidator.validate("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNb", Chain.BTC)
    assert res5.valid is False
    assert res5.checksum_valid is False


def test_tron_address_validation():
    # Valid Tron Base58Check
    res1 = MultiChainValidator.validate("TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t", Chain.TRON)
    assert res1.valid is True
    assert res1.checksum_valid is True
    assert res1.format_type == "BASE58CHECK_TRON"

    # Invalid start char
    res2 = MultiChainValidator.validate("XR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t", Chain.TRX)
    assert res2.valid is False
    assert res2.checksum_valid is False

    # Invalid length
    res3 = MultiChainValidator.validate("TR7NHqjeKQxGTCi8q8", Chain.TRX)
    assert res3.valid is False
    assert res3.checksum_valid is False

    # Checksum tampering
    res4 = MultiChainValidator.validate("TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6u", Chain.TRON)
    assert res4.valid is False
    assert res4.checksum_valid is False

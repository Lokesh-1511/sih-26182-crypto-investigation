# backend/app/blockchain/normalization/amount.py
from decimal import Decimal, ROUND_DOWN
from typing import Union

def to_normalized_amount(
    raw_amount: Union[str, int, float, Decimal],
    decimals: int = 18
) -> Decimal:
    """
    Convert raw integer/base-unit blockchain amount to human-readable Decimal.
    e.g. raw_amount="1000000000", decimals=6 -> Decimal("1000.000000") or Decimal("1000")
    """
    if raw_amount is None:
        return Decimal("0")

    # If it's already a float or decimal string with decimal point, handle appropriately
    str_val = str(raw_amount).strip()
    if "." in str_val:
        # Already normalized representation
        return Decimal(str_val)

    # Integer base units (e.g. wei, satoshis, sun)
    dec_val = Decimal(str_val)
    if decimals <= 0:
        return dec_val

    factor = Decimal(10) ** decimals
    normalized = dec_val / factor
    # Normalize trailing zeros where suitable without loss
    return normalized.normalize() if normalized == normalized.to_integral() else normalized


def to_raw_amount(
    normalized_amount: Union[str, int, float, Decimal],
    decimals: int = 18
) -> str:
    """
    Convert normalized Decimal amount to raw base unit string.
    e.g. normalized_amount=Decimal("1000"), decimals=6 -> "1000000000"
    """
    if normalized_amount is None:
        return "0"

    dec_val = Decimal(str(normalized_amount))
    factor = Decimal(10) ** decimals
    raw_val = (dec_val * factor).quantize(Decimal("1"), rounding=ROUND_DOWN)
    return str(raw_val)

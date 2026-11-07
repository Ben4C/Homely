"""Shared money safety utilities (no transactional ledger implemented)."""
from decimal import Decimal, InvalidOperation


# Purpose: Normalize a nonnegative amount into precise cents; never use float financial math.
# Inputs: Raw amount as Decimal or decimal string, representing USD.
# Outputs: Decimal quantized to two places, or ValueError when invalid/negative.
# Constraints: Redundant trailing zeros are allowed; nonzero fractional cents are never rounded.
def usd(value: Decimal | str) -> Decimal:
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Invalid monetary amount") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError("Money must be finite and nonnegative")
    try:
        cents = amount.quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError("Monetary amount exceeds supported precision") from exc
    if amount != cents:
        raise ValueError("Money may have at most two decimal places")
    return cents

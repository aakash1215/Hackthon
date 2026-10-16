"""Exact money helpers: compute in Fraction, round half-up only for display."""
from decimal import Decimal
from fractions import Fraction


def to_decimal(x: Fraction) -> Decimal:
    """Round an exact Fraction to 2 decimals, half away from zero. No floats."""
    sign = -1 if x < 0 else 1
    cents = abs(Fraction(x)) * 100
    whole = cents.numerator // cents.denominator
    if cents - whole >= Fraction(1, 2):
        whole += 1
    return Decimal(sign * whole).scaleb(-2)


def fmt(x: Fraction) -> str:
    return str(to_decimal(x))


def parse_amount(v) -> Fraction:
    """Accept int, str ('2500', '2,500.50'), Decimal or Fraction."""
    if isinstance(v, Fraction):
        return v
    if isinstance(v, bool):
        raise TypeError("bool is not an amount")
    if isinstance(v, int):
        return Fraction(v)
    if isinstance(v, Decimal):
        return Fraction(v)
    if isinstance(v, str):
        return Fraction(Decimal(v.replace(",", "").strip()))
    if isinstance(v, float):  # JSON numbers; go through repr to avoid binary noise
        return Fraction(Decimal(repr(v)))
    raise TypeError(f"unsupported amount type {type(v)}")

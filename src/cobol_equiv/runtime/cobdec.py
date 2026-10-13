"""Intermediate decimal arithmetic, modelled on GnuCOBOL's cob_decimal.

An intermediate value is an exact integer `value` with a decimal `scale`
(value * 10**-scale). Addition, subtraction and multiplication are exact.
Division follows the rule implemented by GnuCOBOL 3.x (libcob/numeric.c,
cob_decimal_div):

    scale  = scale(dividend) - scale(divisor)
    shift  = 38 + (-scale if scale < 0 else 0)
    result = trunc((dividend_value * 10**shift) / divisor_value)
    result scale = scale + shift

i.e. the quotient keeps at least 38 extra decimal places and is truncated
toward zero, not rounded. This is why COMPUTE X = 1 / 3 * 3 stores 0.99 in a
PIC 9V99 target: the intermediate is 0.999...9 (38 nines), and the final store
truncates. The oracle tests in tests/oracle exercise this rule.

Division by zero yields a NaN marker that every store treats as a size error.
"""

from __future__ import annotations

from decimal import Decimal

COB_MAX_DIGITS = 38


class CobDecimal:
    __slots__ = ("value", "scale", "nan")

    def __init__(self, value: int = 0, scale: int = 0, nan: bool = False):
        self.value = value
        self.scale = scale
        self.nan = nan

    # ---- construction -------------------------------------------------
    @classmethod
    def of(cls, x: "CobDecimal | int | str | Decimal") -> "CobDecimal":
        """A numeric literal or Python number. Strings are COBOL numeric literals."""
        if isinstance(x, CobDecimal):
            return x
        if hasattr(x, "to_cobdec"):
            return x.to_cobdec()
        if isinstance(x, bool):
            raise TypeError("bool is not a numeric value")
        if isinstance(x, int):
            return cls(x, 0)
        if isinstance(x, float):
            raise TypeError("float is not accepted; use str or Decimal literals")
        d = Decimal(x) if isinstance(x, str) else x
        if not isinstance(d, Decimal) or not d.is_finite():
            raise TypeError(f"not a finite numeric value: {x!r}")
        sign, digits, exp = d.as_tuple()
        v = int("".join(map(str, digits)) or "0")
        if exp >= 0:
            v *= 10**exp
            sc = 0
        else:
            sc = -exp
        return cls(-v if sign else v, sc)

    # ---- helpers ------------------------------------------------------
    def _align(self, other: "CobDecimal") -> tuple[int, int, int]:
        if self.scale == other.scale:
            return self.value, other.value, self.scale
        if self.scale < other.scale:
            return self.value * 10 ** (other.scale - self.scale), other.value, other.scale
        return self.value, other.value * 10 ** (self.scale - other.scale), self.scale

    def to_decimal(self) -> Decimal:
        if self.nan:
            raise ArithmeticError("NaN intermediate (division by zero)")
        return scaled_decimal(self.value, self.scale)

    def __repr__(self) -> str:
        return "CobDecimal(NaN)" if self.nan else f"CobDecimal({self.to_decimal()})"

    # ---- arithmetic ---------------------------------------------------
    def __add__(self, other):
        other = CobDecimal.of(other)
        if self.nan or other.nan:
            return CobDecimal(nan=True)
        a, b, sc = self._align(other)
        return CobDecimal(a + b, sc)

    def __radd__(self, other):
        return CobDecimal.of(other) + self

    def __sub__(self, other):
        other = CobDecimal.of(other)
        if self.nan or other.nan:
            return CobDecimal(nan=True)
        a, b, sc = self._align(other)
        return CobDecimal(a - b, sc)

    def __rsub__(self, other):
        return CobDecimal.of(other) - self

    def __mul__(self, other):
        other = CobDecimal.of(other)
        if self.nan or other.nan:
            return CobDecimal(nan=True)
        return CobDecimal(self.value * other.value, self.scale + other.scale)

    def __rmul__(self, other):
        return CobDecimal.of(other) * self

    def __truediv__(self, other):
        other = CobDecimal.of(other)
        if self.nan or other.nan or other.value == 0:
            return CobDecimal(nan=True)
        if self.value == 0:
            return CobDecimal(0, 0)
        scale = self.scale - other.scale
        shift = COB_MAX_DIGITS + (-scale if scale < 0 else 0)
        num = self.value * 10**shift
        q = abs(num) // abs(other.value)
        if (num < 0) != (other.value < 0):
            q = -q
        return CobDecimal(q, scale + shift)

    def __rtruediv__(self, other):
        return CobDecimal.of(other) / self

    def __neg__(self):
        if self.nan:
            return CobDecimal(nan=True)
        return CobDecimal(-self.value, self.scale)

    def __pos__(self):
        return self


def scaled_decimal(value: int, scale: int) -> Decimal:
    """value * 10**-scale as an exact Decimal (Decimal.scaleb would round to
    the context precision, 28 digits by default)."""
    sign = 1 if value < 0 else 0
    digits = tuple(int(c) for c in str(abs(value)))
    return Decimal((sign, digits, -scale))


def dec(x) -> CobDecimal:
    """Shorthand: dec("0.05"), dec(12), dec(field)."""
    return CobDecimal.of(x)

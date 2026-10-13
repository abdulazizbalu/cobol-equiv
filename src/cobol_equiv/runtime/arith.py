"""ADD, SUBTRACT, MULTIPLY, DIVIDE and COMPUTE.

Each function returns True when a size error occurred for any target. Pass
on_size_error=True when the COBOL statement has an ON SIZE ERROR (or
NOT ON SIZE ERROR) phrase: a target whose result does not fit is then left
unchanged. Without the phrase, the result is stored with high-order
truncation (COMP-5: binary wrap-around), as GnuCOBOL does by default.

ROUNDED uses the default COBOL mode, nearest-away-from-zero. Without ROUNDED
excess low-order digits are truncated.

Operands may be FieldRefs, Python ints, Decimals, numeric strings
("0.05") or CobDecimal intermediates. Intermediate results follow
cobdec.CobDecimal (exact +, -, *; division truncated after 38+ extra places).

A target is a FieldRef, or (FieldRef, rounded) to set ROUNDED per target.
Division by zero is always a size error; the target is left unchanged even
without ON SIZE ERROR, matching GnuCOBOL 3.x.
"""

from __future__ import annotations

from .cobdec import CobDecimal, dec
from .move import store_cobdec
from .storage import FieldRef


def _targets(targets, rounded):
    if isinstance(targets, (FieldRef, tuple)):
        targets = [targets]
    out = []
    for t in targets:
        if isinstance(t, tuple):
            out.append((t[0], bool(t[1])))
        else:
            out.append((t, rounded))
    return out


def _sum(operands) -> CobDecimal:
    if not isinstance(operands, (list, tuple)):
        operands = [operands]
    total = dec(operands[0])
    for o in operands[1:]:
        total = total + dec(o)
    return total


def _store_all(results, rounded, on_size_error) -> bool:
    err = False
    for f, r, value in results:
        if value.nan:
            err = True
            continue
        if store_cobdec(f, value, rounded=r, keep_on_overflow=on_size_error):
            err = True
    return err


def add(operands, targets, *, rounded=False, on_size_error=False) -> bool:
    """ADD operands TO targets."""
    s = _sum(operands)
    ts = _targets(targets, rounded)
    return _store_all([(f, r, dec(f) + s) for f, r in ts], rounded, on_size_error)


def add_giving(operands, giving, *, rounded=False, on_size_error=False) -> bool:
    """ADD operands GIVING giving (ADD a TO b GIVING c == add_giving([a, b], c))."""
    s = _sum(operands)
    return _store_all([(f, r, s) for f, r in _targets(giving, rounded)], rounded, on_size_error)


def subtract(operands, targets, *, rounded=False, on_size_error=False) -> bool:
    """SUBTRACT operands FROM targets."""
    s = _sum(operands)
    ts = _targets(targets, rounded)
    return _store_all([(f, r, dec(f) - s) for f, r in ts], rounded, on_size_error)


def subtract_giving(operands, minuend, giving, *, rounded=False, on_size_error=False) -> bool:
    """SUBTRACT operands FROM minuend GIVING giving."""
    v = dec(minuend) - _sum(operands)
    return _store_all([(f, r, v) for f, r in _targets(giving, rounded)], rounded, on_size_error)


def multiply(operand, targets, *, rounded=False, on_size_error=False) -> bool:
    """MULTIPLY operand BY targets."""
    a = dec(operand)
    ts = _targets(targets, rounded)
    return _store_all([(f, r, a * dec(f)) for f, r in ts], rounded, on_size_error)


def multiply_giving(a, b, giving, *, rounded=False, on_size_error=False) -> bool:
    """MULTIPLY a BY b GIVING giving."""
    v = dec(a) * dec(b)
    return _store_all([(f, r, v) for f, r in _targets(giving, rounded)], rounded, on_size_error)


def divide_into(divisor, targets, *, rounded=False, on_size_error=False) -> bool:
    """DIVIDE divisor INTO targets (target = target / divisor)."""
    d = dec(divisor)
    ts = _targets(targets, rounded)
    return _store_all([(f, r, dec(f) / d) for f, r in ts], rounded, on_size_error)


def divide_giving(dividend, divisor, giving, *, rounded=False, on_size_error=False) -> bool:
    """DIVIDE divisor INTO dividend GIVING g, or DIVIDE dividend BY divisor GIVING g."""
    v = dec(dividend) / dec(divisor)
    return _store_all([(f, r, v) for f, r in _targets(giving, rounded)], rounded, on_size_error)


def divide_remainder(dividend, divisor, quotient: FieldRef, remainder: FieldRef, *,
                     rounded=False, on_size_error=False) -> bool:
    """DIVIDE ... GIVING quotient [ROUNDED] REMAINDER remainder.

    As in GnuCOBOL (cob_div_quotient / cob_div_remainder): the remainder is
    dividend - divisor * q, where q is the quotient truncated to the
    quotient item's decimal places (not rounded, not high-order truncated).
    GnuCOBOL 3.1.2 computes and stores the remainder even when the quotient
    had a size error under ON SIZE ERROR (the quotient itself is then left
    unchanged). The COBOL standard says the remainder is left unchanged too;
    this runtime follows GnuCOBOL, the oracle.
    """
    a = dec(dividend)
    b = dec(divisor)
    q = a / b
    if q.nan:
        return True
    err = store_cobdec(quotient, q, rounded=rounded, keep_on_overflow=on_size_error)
    qs = quotient.pic.scale
    if q.scale > qs:
        div = 10 ** (q.scale - qs)
        t = abs(q.value) // div
        qt = CobDecimal(-t if q.value < 0 else t, qs)
    else:
        qt = q
    rem = a - b * qt
    if store_cobdec(remainder, rem, keep_on_overflow=on_size_error):
        err = True
    return err


def compute(targets, value, *, rounded=False, on_size_error=False) -> bool:
    """COMPUTE targets = value, where value is a CobDecimal expression,
    e.g. compute(x, dec(a) * dec(b) / 100, rounded=True)."""
    v = dec(value)
    return _store_all([(f, r, v) for f, r in _targets(targets, rounded)], rounded, on_size_error)

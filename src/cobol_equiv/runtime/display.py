"""The DISPLAY statement's rendering of data items (GnuCOBOL 3.x defaults).

Alphanumeric, alphabetic, numeric-edited and group items are written as their
raw bytes. Numeric items are rendered as GnuCOBOL does with its default
pretty-display setting:

  * a leading '+' or '-' if the PICTURE has S (none otherwise); a negative
    zero is shown as '+', because the value goes through a decimal
    conversion that does not keep the sign of zero;
  * all PICTURE digit positions, with leading zeros;
  * a '.' before the decimal places when the PICTURE has V.

COMP-5 items are rendered with as many digits as the largest value the binary
field can hold (3, 5, 10 and 20 digits for 1, 2, 4 and 8 bytes), because COMP-5 is not
truncated to its PICTURE, and without a decimal point even when the PICTURE
has V (observed with GnuCOBOL 3.1.2; see results/oracle_summary.md).
"""

from __future__ import annotations

from decimal import Decimal

from . import encoding as enc
from .cobdec import CobDecimal
from .move import Figurative, to_bytes
from .pic import NUMERIC
from .storage import FieldRef


# digits shown for COMP-5 items, by byte size (signed and unsigned alike)
COMP5_DISPLAY_DIGITS = {1: 3, 2: 5, 4: 10, 8: 20}


def display_bytes(item) -> bytes:
    if isinstance(item, FieldRef):
        if item.category != NUMERIC:
            return item.raw
        p = item.pic
        neg, mag = item.sign_mag()
        ndig = p.digits
        point = p.scale > 0
        if item.usage == enc.COMP5:
            ndig = COMP5_DISPLAY_DIGITS[item.size]
            point = False
        neg = neg and mag != 0
        s = str(mag).rjust(ndig, "0")[-ndig:]
        if point:
            s = s[: len(s) - p.scale] + "." + s[len(s) - p.scale:]
        if p.signed:
            s = ("-" if neg else "+") + s
        return s.encode("ascii")
    if isinstance(item, (str, bytes)):
        return to_bytes(item)
    if isinstance(item, Figurative):
        return item.byte
    if isinstance(item, (int, Decimal, CobDecimal)):
        raise TypeError("DISPLAY of numeric literals: pass the literal text as a string")
    raise TypeError(f"cannot DISPLAY {item!r}")


def display_line(*items) -> bytes:
    """Bytes written by DISPLAY item... (with the trailing newline)."""
    return b"".join(display_bytes(i) for i in items) + b"\n"

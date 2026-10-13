"""MOVE semantics and the numeric store used by arithmetic statements.

Implemented MOVE categories (anything else raises MoveError):

  numeric        -> numeric          decimal-point alignment, low-order digits
                                     truncated (never rounded), high-order
                                     digits truncated; sign dropped for
                                     unsigned targets; negative zero kept
  numeric        -> numeric-edited   alignment and truncation as above, then
                                     editing (see edit.py)
  numeric-edited -> alphanumeric     byte copy, alphanumeric rules
  numeric int    -> alphanumeric     the unsigned digits, then alphanumeric rules
  alphanumeric   -> numeric          from an item: GnuCOBOL's conversion of the
                                     text (libcob cob_move_alphanum_to_display):
                                     leading spaces, an optional sign, digits,
                                     one decimal point, spaces and commas; any
                                     other character makes the result zero.
                                     From a literal: only when it is all digits
                                     (treated as an unsigned integer)
  alphanumeric/group -> alphanumeric/group
                                     left-justified, space padded, truncated
                                     on the right (a group receiver also takes
                                     any sender as bytes)

Refused with Unsupported: an alphanumeric literal to numeric-edited, and
numeric-edited to numeric or numeric-edited (GnuCOBOL converts these
numerically).
  figuratives    SPACES, ZEROS, HIGH-VALUES, LOW-VALUES, ALL "lit"

Binary truncation (GnuCOBOL default -fbinary-truncate): a COMP item is
truncated to its PICTURE digits like DISPLAY. A COMP-5 item is not: its value
is the whole binary field, and stores wrap modulo 2**bits.
"""

from __future__ import annotations

from decimal import Decimal

from . import encoding as enc
from .cobdec import CobDecimal
from .edit import edit
from .errors import Unsupported
from .pic import ALPHABETIC, ALPHANUMERIC, NUMERIC, NUMERIC_EDITED
from .storage import GROUP, FieldRef


class MoveError(TypeError):
    pass


class Figurative:
    def __init__(self, name: str, byte: bytes):
        self.name = name
        self.byte = byte

    def __repr__(self) -> str:
        return self.name


SPACES = Figurative("SPACES", b" ")
ZEROS = Figurative("ZEROS", b"0")
HIGH_VALUES = Figurative("HIGH-VALUES", b"\xff")
LOW_VALUES = Figurative("LOW-VALUES", b"\x00")


class All(Figurative):
    """ALL "literal"."""

    def __init__(self, lit: str | bytes):
        b = lit.encode("latin-1") if isinstance(lit, str) else lit
        super().__init__(f"ALL {b!r}", b)


def _fill(pattern: bytes, n: int) -> bytes:
    return (pattern * (n // len(pattern) + 1))[:n]


def to_bytes(text: str | bytes) -> bytes:
    """Alphanumeric literal to bytes (one byte per character, latin-1)."""
    return text if isinstance(text, (bytes, bytearray)) else text.encode("latin-1")


# ---- numeric store ------------------------------------------------------

def _scale_to(value: int, from_scale: int, to_scale: int, rounded: bool) -> int:
    if to_scale >= from_scale:
        return value * 10 ** (to_scale - from_scale)
    div = 10 ** (from_scale - to_scale)
    q, r = divmod(abs(value), div)
    if rounded and 2 * r >= div:  # nearest, ties away from zero
        q += 1
    return -q if value < 0 else q


def store_numeric(dst: FieldRef, neg: bool, mag: int, scale: int, *,
                  rounded: bool = False, keep_on_overflow: bool = False,
                  sign_mode: str = "arith", edit_extra: bool = False) -> bool:
    """Store sign/magnitude into a numeric or numeric-edited item.

    Returns True on size error (value does not fit). With keep_on_overflow the
    target is then left unchanged, as for ON SIZE ERROR; otherwise high-order
    digits are truncated (COMP-5: binary wrap-around).

    Sign of a zero result (only visible in DISPLAY and COMP-3 items):
      sign_mode="arith"   arithmetic statements: the sign of the value after
                          decimal alignment, before high-order truncation, so
                          -10000 into S9(4) gives a negative zero but -0.004
                          into S9V99 a positive one;
      sign_mode="sender"  MOVE item to item where GnuCOBOL copies the sender's
                          sign even if every kept digit is zero (see move()).
    """
    p = dst.pic
    signed_val = -mag if neg else mag
    v = _scale_to(signed_val, scale, p.scale, rounded)
    m = abs(v)
    if sign_mode == "sender":
        is_neg = neg
    else:
        is_neg = v < 0
    if dst.category == NUMERIC_EDITED:
        overflow = m >= 10 ** p.digits
        if overflow and keep_on_overflow:
            return True
        # the first sender digit right of the receiver's last place: GnuCOBOL's
        # editing reads it for a trailing + or - (see edit.py)
        # (MOVE only; arithmetic results are stored at the receiver's scale)
        extra = (mag // 10 ** (scale - p.scale - 1)) % 10 if edit_extra and scale > p.scale else 0
        dst.set_raw(edit(p, is_neg, m, extra))
        return overflow
    u = dst.usage
    if u == enc.COMP5:
        # GnuCOBOL's size check for COMP-5 is symmetric: a signed 2-byte item
        # accepts -32767..32767 under ON SIZE ERROR although -32768 fits.
        _, hi = enc.binary_range(dst.size, p.signed)
        val = -m if (is_neg and p.signed) else m
        overflow = m > hi
        if m >= 1 << 63 and not keep_on_overflow:
            raise Unsupported(f"store of a value >= 2**63 into binary item {dst.name}")
        if overflow and keep_on_overflow:
            return True
        dst.set_raw(enc.encode_binary(val, dst.size, p.signed, native=True))
        return overflow
    overflow = m >= 10 ** p.digits
    if overflow and keep_on_overflow:
        return True
    if u == enc.COMP and m >= 1 << 63:
        # GnuCOBOL 3.1.2 converts through a 64-bit integer here; the result is
        # not a decimal truncation (docs/runtime.md, "MOVE").
        raise Unsupported(f"store of a value >= 2**63 into binary item {dst.name}")
    m %= 10 ** p.digits
    if u == enc.DISPLAY:
        dst.set_raw(enc.encode_display(is_neg, m, p.digits, p.signed))
    elif u == enc.COMP3:
        dst.set_raw(enc.encode_packed(is_neg, m, p.digits, p.signed))
    else:
        val = -m if (is_neg and p.signed) else m
        dst.set_raw(enc.encode_binary(val, dst.size, p.signed, native=False))
    return overflow


def store_cobdec(dst: FieldRef, d: CobDecimal, *, rounded=False, keep_on_overflow=False) -> bool:
    if d.nan:
        return True  # division by zero: size error, target unchanged
    return store_numeric(dst, d.value < 0, abs(d.value), d.scale,
                         rounded=rounded, keep_on_overflow=keep_on_overflow)


# ---- MOVE -----------------------------------------------------------------

def _is_alnum_like(f: FieldRef) -> bool:
    return f.category in (ALPHANUMERIC, ALPHABETIC, GROUP)


def _alnum_store(dst: FieldRef, data: bytes) -> None:
    n = dst.size
    dst.set_raw(data[:n].ljust(n, b" "))


def _numeric_digits_text(src: FieldRef) -> bytes:
    """Digits of an integer numeric item as moved to alphanumeric."""
    p = src.pic
    if p.scale:
        raise MoveError(f"MOVE of non-integer numeric {src.name} to alphanumeric")
    neg, mag = src.sign_mag()
    ndig = p.digits  # also for COMP-5, whose value may exceed the PICTURE
    return str(mag).rjust(ndig, "0")[-ndig:].encode("ascii")


def move(src, *dsts: FieldRef) -> None:
    for dst in dsts:
        _move1(src, dst)


def _move1(src, dst: FieldRef) -> None:
    dcat = dst.category
    # figuratives
    if isinstance(src, Figurative):
        if src is ZEROS and dcat in (NUMERIC, NUMERIC_EDITED):
            store_numeric(dst, False, 0, 0)
        elif dcat in (NUMERIC, NUMERIC_EDITED):
            raise MoveError(f"MOVE {src.name} to numeric {dst.name}")
        else:
            dst.set_raw(_fill(src.byte, dst.size))
        return
    # alphanumeric literal
    if isinstance(src, (str, bytes)):
        data = to_bytes(src)
        if dcat == NUMERIC:
            _alnum_to_numeric(data, dst)
        elif dcat == NUMERIC_EDITED:
            raise Unsupported(_TO_EDITED.format(dst.name))
        else:
            _alnum_store(dst, data)
        return
    # numeric literal / intermediate
    if isinstance(src, (int, Decimal, CobDecimal)) and not isinstance(src, bool):
        d = CobDecimal.of(src)
        if dcat in (NUMERIC, NUMERIC_EDITED):
            # cobc converts literal MOVEs at compile time. When the literal has
            # more integer digits than the receiver (cobc warns "value size
            # exceeds data size") the sign of the truncated result differs
            # between items in GnuCOBOL 3.1.2, so that case is refused.
            ip = dst.pic.digits - dst.pic.scale
            if abs(d.value) // 10 ** d.scale >= 10 ** ip:
                raise Unsupported(f"numeric literal {d.to_decimal()} does not fit {dst.name}")
            # a literal that truncates to zero keeps its sign: MOVE -0.004 to
            # S9V99 stores a negative zero (oracle rule encode_literal)
            store_numeric(dst, d.value < 0, abs(d.value), d.scale, sign_mode="sender",
                          edit_extra=True)
        else:
            raise MoveError("MOVE of a numeric literal to alphanumeric: write it as a string")
        return
    if not isinstance(src, FieldRef):
        raise MoveError(f"unsupported MOVE source {src!r}")
    scat = src.category
    if scat == GROUP or dcat == GROUP:
        _alnum_store(dst, src.raw)
        return
    if scat == NUMERIC:
        if dcat in (NUMERIC, NUMERIC_EDITED):
            neg, mag = src.sign_mag()
            # GnuCOBOL 3.1.2 (oracle rule move_num_to_num, "zero sign" cases):
            # a USAGE DISPLAY receiver always gets the sender's sign, so a
            # truncated negative value becomes a negative zero; a COMP-3
            # receiver does so only from a DISPLAY sender; otherwise the sign
            # comes from the aligned value, as in arithmetic.
            keep = dst.usage == enc.DISPLAY or (
                dst.usage == enc.COMP3 and src.usage == enc.DISPLAY)
            store_numeric(dst, neg, mag, src.pic.scale,
                          sign_mode="sender" if keep else "arith", edit_extra=True)
        elif dcat == ALPHANUMERIC:
            _alnum_store(dst, _numeric_digits_text(src))
        else:
            raise MoveError(f"MOVE numeric {src.name} to alphabetic {dst.name}")
        return
    if scat in (ALPHANUMERIC, ALPHABETIC):
        if dcat in (NUMERIC, NUMERIC_EDITED):
            alnum_text_to_numeric(src.raw, dst)
        else:
            _alnum_store(dst, src.raw)
        return
    if scat == NUMERIC_EDITED:
        if dcat in (ALPHANUMERIC, ALPHABETIC):
            _alnum_store(dst, src.raw)
            return
        raise Unsupported(f"MOVE from numeric-edited {src.name} to {dcat} {dst.name} "
                          "(GnuCOBOL de-edits the sender; not modelled)")
    raise MoveError(f"MOVE {scat} -> {dcat} not supported")


_TO_EDITED = ("MOVE of alphanumeric data to numeric-edited {} (GnuCOBOL converts the "
              "sender to a number and edits it; not modelled)")


def _alnum_to_numeric(data: bytes, dst: FieldRef) -> None:
    if not data or not data.isdigit():
        raise MoveError(
            f"MOVE of non-digit alphanumeric data {data!r} to numeric {dst.name}: "
            "result is implementation-specific in GnuCOBOL and not modelled"
        )
    store_numeric(dst, False, int(data), 0)


def parse_alnum_number(text: bytes, int_digits: int, scale: int):
    """libcob `cob_move_alphanum_to_display` into a DISPLAY item with
    int_digits integer and `scale` decimal digits. Returns (negative, digits
    as int) or None when the text is not a number (the result is then zero).

    Leading white space is skipped, then an optional + or -. The digits
    before the decimal point are right-aligned to the integer places (excess
    leading digits are dropped); digits after it fill the decimal places
    (excess dropped). Spaces and commas are skipped; a second decimal point
    or any other character makes the text invalid, but only if it is reached
    before the receiver is full."""
    s, e = 0, len(text)
    while s < e and chr(text[s]).isspace():
        s += 1
    sign = 0
    if s < e and text[s] in (0x2B, 0x2D):
        sign = 1 if text[s] == 0x2B else -1
        s += 1
    count = sum(1 for c in text[s:].split(b".")[0] if 0x30 <= c <= 0x39)
    out = bytearray(b"0" * (int_digits + scale))
    o = int_digits - count if count < int_digits else 0
    while count > int_digits:
        while not 0x30 <= text[s] <= 0x39:
            s += 1
        s += 1
        count -= 1
    dots = 0
    while s < e and o < len(out):
        c = text[s]
        if 0x30 <= c <= 0x39:
            out[o] = c
            o += 1
        elif c == 0x2E:
            dots += 1
            if dots > 1:
                return None
        elif not (chr(c).isspace() or c == 0x2C):
            return None
        s += 1
    return sign < 0, int(out)


def alnum_text_to_numeric(text: bytes, dst: FieldRef) -> None:
    """MOVE of an alphanumeric item to a numeric or numeric-edited item.
    A USAGE DISPLAY receiver gets the conversion directly (the sign of a
    zero result is kept). Other receivers get it through a signed DISPLAY
    temporary of 38 integer and 38 decimal digits, then a numeric MOVE."""
    p = dst.pic
    if dst.category == NUMERIC and dst.usage == enc.DISPLAY:
        r = parse_alnum_number(text, p.digits - p.scale, p.scale)
        neg, mag = r if r is not None else (False, 0)
        store_numeric(dst, neg, mag, p.scale, sign_mode="sender")
        return
    r = parse_alnum_number(text, 38, 38)
    neg, mag = r if r is not None else (False, 0)
    keep = dst.usage in (enc.DISPLAY, enc.COMP3)
    store_numeric(dst, neg, mag, 38, sign_mode="sender" if keep else "arith", edit_extra=True)


def apply_value(value, f: FieldRef) -> None:
    """A VALUE clause. Like MOVE, except for numeric-edited items: there a
    figurative constant fills the item with its character (VALUE ZERO gives
    "000000", not an edited zero) and an alphanumeric literal is stored as
    written, as GnuCOBOL does (oracle rule value_clause)."""
    if f.category == NUMERIC_EDITED and isinstance(value, Figurative):
        f.set_raw(_fill(value.byte, f.size))
    elif f.category == NUMERIC_EDITED and isinstance(value, (str, bytes)):
        _alnum_store(f, to_bytes(value))
    else:
        move(value, f)


def set_initial(f: FieldRef) -> None:
    """GnuCOBOL default WORKING-STORAGE initialisation of one elementary item."""
    if f.category in (NUMERIC, NUMERIC_EDITED):
        store_numeric(f, False, 0, 0)
    else:
        f.set_raw(b" " * f.size)


def initialize(f: FieldRef) -> None:
    """INITIALIZE: alphanumeric -> spaces, numeric/edited -> zero, for every
    elementary item under `f` (FILLER items skipped, REDEFINES skipped)."""
    from .storage import _child_offsets

    if f.item.pic is not None:
        set_initial(f)
        return

    def walk(item, base):
        for c, coff in _child_offsets(item):
            if c.redefines:
                continue
            n = c.occurs or 1
            sz = c.elem_size()
            for i in range(n):
                off = base + coff + i * sz
                if c.pic is None:
                    walk(c, off)
                elif c.name != "FILLER":
                    set_initial(FieldRef(f.area, off, sz, c, c.name))

    walk(f.item, f.offset)

"""Numeric editing (MOVE to a numeric-edited item).

The algorithm follows the structure of GnuCOBOL's cob_move_display_to_edited
(libcob/move.c) for the supported subset:

  9            digit
  Z  *         zero suppression with space / asterisk (check protection)
  $            fixed (single) or floating (repeated) currency sign
  +  -         fixed (single, leading or trailing) or floating (repeated) sign
  CR DB        credit / debit, shown only for negative non-zero values
  .            decimal point
  ,  B  0  /   insertion characters

Behaviours worth knowing (all checked against GnuCOBOL by the oracle tests):
  * if every digit position is suppressed (no 9, value zero) the whole item
    becomes spaces, or all '*' except the decimal point for check protection;
  * once a non-zero digit or a 9 position is reached, suppression ends and
    Z / * positions right of the decimal point print digits;
  * a floating sign or currency symbol is written into the rightmost space
    left of the first printed character; a fixed one stays in position 0;
  * the first symbol of a floating string, and a fixed leading sign or $,
    each take one high-order digit from the sender. That digit is never
    printed, but if it is non-zero it ends zero suppression: 1000 edited
    with ---9 gives " 000", not "   0".

Not supported (Unsupported is raised): BLANK WHEN ZERO, P, trailing
currency, a fixed sign or $ combined with a floating string (for example
-$$$9.99, where GnuCOBOL 3.1.2 prints '-' for positive values), B right of
the decimal point, DECIMAL-POINT IS COMMA, CURRENCY SIGN clauses.
"""

from __future__ import annotations

from .errors import Unsupported
from .pic import Pic


def _integer_positions(pic: Pic) -> int:
    """Digits GnuCOBOL takes from the sender left of the decimal point: every
    9 Z *, plus leading sign / currency symbols seen before the first of them
    (so a floating string's first symbol, and a fixed leading sign or $, each
    consume one high-order digit that is never printed)."""
    count = 0
    count_sign = count_curr = True
    for s in pic.symbols:
        if s in ("9", "Z", "*"):
            count += 1
            count_sign = count_curr = False
        elif s == "$" and count_curr:
            count += 1
        elif s in ("+", "-") and count_sign:
            count += 1
        elif s in (".", "V"):
            break
    return count


def _check_supported(pic: Pic) -> None:
    syms = pic.symbols
    floating = {c for c in "$+-" if syms.count(c) >= 2}
    fixed_lead = syms[0] in ("$", "+", "-") and syms[0] not in floating
    if fixed_lead and floating:
        raise Unsupported(
            f"PICTURE {pic.text}: a fixed leading sign or currency symbol combined with a "
            "floating string gives non-standard results in GnuCOBOL 3.1.2 (pinned by tests/oracle/test_gnucobol_quirks.py)")
    if len(floating) > 1:
        raise Unsupported(f"PICTURE {pic.text}: two floating strings")
    for c in ("$", "+", "-"):
        n = syms.count(c)
        if n == 1 and c in ("+", "-") and syms[0] != c and syms[-1] != c:
            raise Unsupported(f"PICTURE {pic.text}: sign symbol must be first or last")
        if n == 1 and c == "$" and syms[0] != "$":
            raise Unsupported(f"PICTURE {pic.text}: fixed $ must be first")
    if "B" in syms and "." in syms and syms.index("B") > syms.index("."):
        raise Unsupported(f"PICTURE {pic.text}: B after the decimal point")


def edit(pic: Pic, neg: bool, mag: int, extra: int = 0) -> bytes:
    """Edit an unsigned magnitude in units of 10**-pic.scale (not yet
    truncated: high-order digits beyond the picture are dropped here) with
    sign `neg` into the picture's character form.

    `extra` is the sender's next digit after the receiver's last decimal
    place (0 if none). GnuCOBOL reads it for a trailing + or - sign, so
    -0.5 edited with ZZZ9- gives "   0-" (oracle rule edit_trailing_sign)."""
    _check_supported(pic)
    width = _integer_positions(pic) + pic.scale
    digits = (str(mag).rjust(width, "0")[-width:] if width else "") + str(extra)
    it = iter(digits)

    def take() -> str:
        return next(it, "0")

    syms = pic.symbols
    floating = {c for c in "$+-" if syms.count(c) >= 2}
    out: list[str] = []
    suppress = True
    is_zero = True
    pad = " "
    trailing = False
    decimal_point: int | None = None
    float_sign = ""
    float_curr = ""
    sign_first = False
    fixed_sign: tuple[int, str] | None = None
    end = pic.size
    seen = set()

    for s in syms:
        pos = len(out)
        if s in ("0", "/"):
            out.append(s)
        elif s == "B":
            out.append(pad if suppress else "B")
        elif s == "9":
            d = take()
            out.append(d)
            if d != "0":
                is_zero = False
            suppress = False
            trailing = True
        elif s in ("Z", "*"):
            d = take()
            if d != "0":
                is_zero = suppress = False
            pad = "*" if s == "*" else " "
            out.append(pad if suppress else d)
            trailing = True
        elif s == ".":
            out.append(".")
            decimal_point = pos
        elif s == "V":
            decimal_point = pos - 1
        elif s == ",":
            out.append(pad if suppress else ",")
        elif s in ("CR", "DB"):
            end = pos
            out.extend(s if (neg and not is_zero) else "  ")
        elif s in ("+", "-") and trailing:
            if take() != "0":
                is_zero = suppress = False
            if neg and not is_zero:
                out.append("-")
            else:
                out.append("+" if s == "+" else " ")
            end -= 1
        elif s in floating:
            d = take()
            if s not in seen:
                # first symbol of a floating string: consumes a digit that is
                # never printed but, if non-zero, ends zero suppression
                seen.add(s)
                if d != "0":
                    is_zero = suppress = False
                out.append(pad)
                if s == "$":
                    float_curr = "$"
                else:
                    float_sign = s
                    sign_first = not float_curr
            elif suppress and d == "0":
                out.append(pad)
            else:
                out.append(d)
                if d != "0":
                    is_zero = suppress = False
        elif s in ("+", "-", "$"):
            # fixed leading symbol in position 0
            d = take()
            if d != "0":
                is_zero = suppress = False
            out.append(" ")
            fixed_sign = (pos, s)
        else:
            raise Unsupported(f"edit symbol {s!r}")

    if suppress:
        if pad == " ":
            return b" " * pic.size
        return "".join(c if c == "." else pad for c in out).encode("ascii")

    if decimal_point is not None:
        for j in range(decimal_point + 1, end):
            if out[j] in (" ", "*"):
                out[j] = "0"

    if fixed_sign is not None:
        j, s = fixed_sign
        if s == "$":
            out[j] = "$"
        elif neg and not is_zero:
            out[j] = "-"
        else:
            out[j] = "+" if s == "+" else " "

    if float_sign:
        float_sign = "-" if (neg and not is_zero) else ("+" if float_sign == "+" else " ")
    if float_sign or float_curr:
        j = end - 1
        while j > 0 and out[j] != " ":
            j -= 1
        if float_sign and float_curr:
            first, second = (float_curr, float_sign) if sign_first else (float_sign, float_curr)
            out[j] = first
            if j - 1 >= 0:
                out[j - 1] = second
        else:
            out[j] = float_sign or float_curr

    count = 0
    for j in range(end):
        if out[j] == "B":
            out[j] = pad if count == 0 else " "
        else:
            count += 1
    return "".join(out).encode("ascii")

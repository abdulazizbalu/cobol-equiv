"""PICTURE string parsing.

Supported symbols: 9 S V X A Z * $ , . + - CR DB B 0 /, with repeat counts
such as 9(5) or X(10). Not supported: P (scaling positions), N/national,
E (floating point editing), currency signs other than $, DECIMAL-POINT IS
COMMA. Unsupported symbols raise PicError rather than being guessed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

NUMERIC = "numeric"
ALPHANUMERIC = "alphanumeric"
ALPHABETIC = "alphabetic"
NUMERIC_EDITED = "numeric-edited"

_EDIT_SYMBOLS = set("Z*$,.+-B0/") | {"CR", "DB"}
_TOKEN = re.compile(r"CR|DB|\(\d+\)|.", re.IGNORECASE)


class PicError(ValueError):
    pass


@dataclass(frozen=True)
class Pic:
    text: str
    symbols: tuple[str, ...]  # expanded, upper case; CR and DB are one symbol each
    category: str
    digits: int  # digit positions (numeric and numeric-edited)
    scale: int  # digit positions right of V or '.'
    signed: bool  # numeric: has S; edited: has + - CR DB
    size: int  # characters in USAGE DISPLAY form (S and V take no space)

    @property
    def is_numeric(self) -> bool:
        return self.category == NUMERIC


def expand(text: str) -> tuple[str, ...]:
    out: list[str] = []
    for tok in _TOKEN.findall(text.strip()):
        if tok.startswith("("):
            if not out:
                raise PicError(f"repeat count without symbol in {text!r}")
            out.extend([out[-1]] * (int(tok[1:-1]) - 1))
        else:
            out.append(tok.upper())
    return tuple(out)


def parse_pic(text: str) -> Pic:
    syms = expand(text)
    if not syms:
        raise PicError("empty PICTURE")
    unknown = [s for s in syms if s not in _EDIT_SYMBOLS and s not in "9SVXA"]
    if unknown:
        raise PicError(f"unsupported PICTURE symbol(s) {sorted(set(unknown))} in {text!r}")
    sset = set(syms)

    if sset <= set("9SV"):
        if "S" in syms and syms[0] != "S" or syms.count("S") > 1:
            raise PicError(f"S must be the first symbol: {text!r}")
        if syms.count("V") > 1:
            raise PicError(f"more than one V: {text!r}")
        digits = syms.count("9")
        if digits == 0 or digits > 38:
            raise PicError(f"numeric PICTURE needs 1..38 digits: {text!r}")
        scale = len(syms) - syms.index("V") - 1 if "V" in syms else 0
        return Pic(text, syms, NUMERIC, digits, scale, "S" in syms, digits)

    if sset <= set("XA9"):
        cat = ALPHABETIC if sset == {"A"} else ALPHANUMERIC
        return Pic(text, syms, cat, 0, 0, False, len(syms))

    if sset & set("XAS"):
        raise PicError(f"cannot mix X/A/S with editing symbols: {text!r}")
    return _parse_edited(text, syms)


def _parse_edited(text: str, syms: tuple[str, ...]) -> Pic:
    if syms.count(".") + syms.count("V") > 1:
        raise PicError(f"more than one decimal point: {text!r}")
    # Floating strings: a run of two or more $, + or - (insertion chars allowed
    # inside). The first symbol of the run is not a digit position.
    digits = 0
    scale = 0
    after_point = False
    floating = _floating_char(syms)
    seen_float = False
    for s in syms:
        if s in (".", "V"):
            after_point = True
            continue
        is_digit = s in ("9", "Z", "*")
        if floating and s == floating:
            if seen_float:
                is_digit = True
            seen_float = True
        if is_digit:
            digits += 1
            if after_point:
                scale += 1
    signed = bool(set(syms) & {"+", "-", "CR", "DB"})
    size = sum(2 if s in ("CR", "DB") else (0 if s == "V" else 1) for s in syms)
    if digits == 0:
        raise PicError(f"numeric-edited PICTURE without digit positions: {text!r}")
    return Pic(text, syms, NUMERIC_EDITED, digits, scale, signed, size)


def _floating_char(syms: tuple[str, ...]) -> str | None:
    for c in ("$", "+", "-"):
        if syms.count(c) >= 2:
            return c
    return None

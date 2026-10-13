"""Byte-level encodings of numeric USAGEs, as produced by GnuCOBOL -std=default.

All numeric storage is described by a sign flag and an unsigned magnitude
(an integer in units of 10**-scale). Keeping the sign separate matters: COBOL
DISPLAY and COMP-3 items can hold a negative zero (for example after a
high-order truncation of -10000 into PIC S9(4)), and MOVE preserves it.

USAGE DISPLAY, signed: trailing embedded sign ("overpunch"). GnuCOBOL's
default (ASCII) convention keeps the digit for positive values and adds 0x40
for negative ones: digit 0..9 -> 'p'..'y'. IBM mainframes use the EBCDIC
convention ('{', 'A'..'I' positive, '}', 'J'..'R' negative); that is not what
GnuCOBOL writes by default and is not implemented here.

USAGE COMP-3 (PACKED-DECIMAL): two digits per byte, last nibble is the sign:
C positive, D negative, F unsigned. A PIC with an even number of digits gets
one leading zero nibble.

USAGE COMP / BINARY: big-endian two's complement (signed) or unsigned.
USAGE COMP-5: native byte order (little-endian on x86-64 / arm64 Linux).
Byte size by number of digits (GnuCOBOL binary-size 1-2-4-8):
1-2 digits -> 1 byte, 3-4 -> 2, 5-9 -> 4, 10-18 -> 8.
"""

from __future__ import annotations

import sys

DISPLAY = "DISPLAY"
COMP3 = "COMP-3"
COMP = "COMP"
COMP5 = "COMP-5"
NUMERIC_USAGES = (DISPLAY, COMP3, COMP, COMP5)

NATIVE_BYTEORDER = sys.byteorder


class DataError(ValueError):
    """Storage holds bytes that are not valid for the item's USAGE."""


def binary_size(digits: int) -> int:
    if digits <= 2:
        return 1
    if digits <= 4:
        return 2
    if digits <= 9:
        return 4
    if digits <= 18:
        return 8
    raise ValueError(f"binary items support at most 18 digits, got {digits}")


def packed_size(digits: int) -> int:
    return digits // 2 + 1


def binary_range(nbytes: int, signed: bool) -> tuple[int, int]:
    bits = 8 * nbytes
    if signed:
        return -(1 << (bits - 1)), (1 << (bits - 1)) - 1
    return 0, (1 << bits) - 1


# ---- DISPLAY -----------------------------------------------------------

def encode_display(neg: bool, mag: int, digits: int, signed: bool) -> bytes:
    s = str(mag).rjust(digits, "0")[-digits:]
    b = bytearray(s, "ascii")
    if signed and neg:
        b[-1] += 0x40
    return bytes(b)


def decode_display(raw: bytes, signed: bool) -> tuple[bool, int]:
    b = bytearray(raw)
    neg = False
    last = b[-1]
    if signed and 0x70 <= last <= 0x79:
        neg = True
        b[-1] = last - 0x40
    if not all(0x30 <= c <= 0x39 for c in b):
        raise DataError(f"invalid USAGE DISPLAY numeric data: {bytes(raw)!r}")
    return neg, int(b.decode("ascii"))


# ---- COMP-3 ------------------------------------------------------------

def encode_packed(neg: bool, mag: int, digits: int, signed: bool) -> bytes:
    nbytes = packed_size(digits)
    s = str(mag).rjust(digits, "0")[-digits:].rjust(2 * nbytes - 1, "0")
    sign = 0xF if not signed else (0xD if neg else 0xC)
    nibbles = [int(c) for c in s] + [sign]
    return bytes((nibbles[i] << 4) | nibbles[i + 1] for i in range(0, len(nibbles), 2))


def decode_packed(raw: bytes) -> tuple[bool, int]:
    nibbles = []
    for byte in raw:
        nibbles += [byte >> 4, byte & 0xF]
    sign = nibbles.pop()
    if any(n > 9 for n in nibbles) or sign < 0xA:
        raise DataError(f"invalid COMP-3 data: {bytes(raw).hex()}")
    mag = 0
    for n in nibbles:
        mag = mag * 10 + n
    return sign in (0xB, 0xD), mag


# ---- binary ------------------------------------------------------------

def encode_binary(value: int, nbytes: int, signed: bool, native: bool) -> bytes:
    """Encode `value`, wrapping modulo 2**(8*nbytes) like a C integer store."""
    value &= (1 << (8 * nbytes)) - 1
    if signed and value >= 1 << (8 * nbytes - 1):
        value -= 1 << (8 * nbytes)
    order = NATIVE_BYTEORDER if native else "big"
    return value.to_bytes(nbytes, order, signed=signed)


def decode_binary(raw: bytes, signed: bool, native: bool) -> int:
    order = NATIVE_BYTEORDER if native else "big"
    return int.from_bytes(raw, order, signed=signed)

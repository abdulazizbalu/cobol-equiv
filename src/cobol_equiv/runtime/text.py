"""STRING, UNSTRING and INSPECT on alphanumeric data.

Byte semantics (one byte per character). Checked against GnuCOBOL by the
oracle rules `string_stmt`, `unstring_stmt`, `inspect_*` for the forms listed
in each function; other forms are not implemented.

Operands that are "text" may be a FieldRef (its stored bytes; for numeric
DISPLAY items the digit characters), a str/bytes literal, or a Figurative.
"""

from __future__ import annotations

from dataclasses import dataclass

from .move import Figurative, move, to_bytes
from .storage import FieldRef


def _text(x) -> bytes:
    if isinstance(x, FieldRef):
        return x.raw
    if isinstance(x, Figurative):
        return x.byte
    return to_bytes(x)


def _ptr_get(ptr: FieldRef | None) -> int:
    return 1 if ptr is None else int(ptr.value)


def _ptr_set(ptr: FieldRef | None, value: int) -> None:
    if ptr is not None:
        move(value, ptr)


# ---- STRING --------------------------------------------------------------

def string(parts, into: FieldRef, pointer: FieldRef | None = None) -> bool:
    """STRING src DELIMITED BY {SIZE | delim} ... INTO into [WITH POINTER pointer].

    parts: list of (source, delimiter) where delimiter is None for SIZE.
    Receiver positions not written keep their contents. Returns True on
    overflow (receiver full while data remains, or pointer out of range).
    """
    buf = bytearray(into.raw)
    p = _ptr_get(pointer)
    if p < 1 or p > len(buf):
        return True
    overflow = False
    for src, delim in parts:
        data = _text(src)
        if delim is not None:
            d = _text(delim)
            k = data.find(d)
            if k >= 0:
                data = data[:k]
        for b in data:
            if p > len(buf):
                overflow = True
                break
            buf[p - 1] = b
            p += 1
        if overflow:
            break
    into.set_raw(bytes(buf))
    _ptr_set(pointer, p)
    return overflow


# ---- UNSTRING ------------------------------------------------------------

@dataclass
class Into:
    """One UNSTRING receiver: INTO field [DELIMITER IN delimiter_in] [COUNT IN count_in]."""
    field: FieldRef
    delimiter_in: FieldRef | None = None
    count_in: FieldRef | None = None


def unstring(source, delimiters, targets, pointer: FieldRef | None = None,
             tallying: FieldRef | None = None) -> bool:
    """UNSTRING source [DELIMITED BY [ALL] d1 [OR [ALL] d2 ...]] INTO targets ...

    delimiters: list of str/bytes/FieldRef, or (delim, True) for ALL delim;
    empty list means no DELIMITED BY phrase (receivers are filled by size).
    targets: list of FieldRef or Into. Returns True on overflow.
    """
    data = _text(source)
    dl = []
    for d in delimiters:
        if isinstance(d, tuple):
            dl.append((_text(d[0]), bool(d[1])))
        else:
            dl.append((_text(d), False))
    tg = [t if isinstance(t, Into) else Into(t) for t in targets]
    p = _ptr_get(pointer)
    if p < 1 or p > len(data):
        return True
    pos = p - 1
    filled = 0
    for t in tg:
        if pos >= len(data):
            break
        if dl:
            hit = None
            for k in range(pos, len(data)):
                for d, is_all in dl:
                    if d and data.startswith(d, k):
                        hit = (k, d, is_all)
                        break
                if hit:
                    break
            if hit:
                k, d, is_all = hit
                piece = data[pos:k]
                nxt = k + len(d)
                if is_all:
                    while data.startswith(d, nxt):
                        nxt += len(d)
                matched = d
            else:
                piece, nxt, matched = data[pos:], len(data), b""
        else:
            size = t.field.size
            piece = data[pos:pos + size]
            nxt, matched = pos + len(piece), b""
        move(piece, t.field)
        if t.delimiter_in is not None:
            move(matched, t.delimiter_in)
        if t.count_in is not None:
            move(len(piece), t.count_in)
        filled += 1
        pos = nxt
    _ptr_set(pointer, pos + 1)
    if tallying is not None:
        move(int(tallying.value) + filled, tallying)
    return pos < len(data)


# ---- INSPECT -------------------------------------------------------------

@dataclass
class Phrase:
    """One INSPECT phrase.

    mode: "ALL", "LEADING", "FIRST" (REPLACING only) or "CHARACTERS".
    pattern: the searched text (ignored for CHARACTERS).
    by: replacement (REPLACING); counter: FieldRef (TALLYING).
    before / after: INITIAL delimiters.
    """
    mode: str
    pattern: object = None
    by: object = None
    counter: FieldRef | None = None
    before: object = None
    after: object = None


def _region(data: bytes, ph: Phrase) -> tuple[int, int]:
    start, end = 0, len(data)
    if ph.after is not None:
        a = _text(ph.after)
        k = data.find(a)
        start = len(data) if k < 0 else k + len(a)
    if ph.before is not None:
        b = _text(ph.before)
        k = data.find(b, start)
        if k >= 0:
            end = k
    return start, end


def _scan(data: bytes, phrases: list[Phrase]):
    """Yield (phrase index, position, length) for each match, left to right,
    phrases tried in order at each position (COBOL INSPECT rules)."""
    regions = [_region(data, ph) for ph in phrases]
    pats = [b"" if ph.mode == "CHARACTERS" else _text(ph.pattern) for ph in phrases]
    leading_alive = [True] * len(phrases)
    first_done = [False] * len(phrases)
    pos = 0
    while pos < len(data):
        hit = None
        for i, ph in enumerate(phrases):
            s, e = regions[i]
            if not s <= pos < e:
                continue
            if ph.mode == "CHARACTERS":
                hit = (i, 1)
                break
            n = len(pats[i])
            if pos + n > e or data[pos:pos + n] != pats[i]:
                continue
            if ph.mode == "LEADING" and not leading_alive[i]:
                continue
            if ph.mode == "FIRST" and first_done[i]:
                continue
            hit = (i, n)
            break
        for i, ph in enumerate(phrases):
            s, _ = regions[i]
            if ph.mode == "LEADING" and pos >= s and (hit is None or hit[0] != i):
                leading_alive[i] = False
        if hit is None:
            pos += 1
            continue
        i, n = hit
        if phrases[i].mode == "FIRST":
            first_done[i] = True
        yield i, pos, n
        pos += n


def inspect_tallying(field, phrases: list[Phrase]) -> None:
    """INSPECT field TALLYING counter FOR {ALL|LEADING} pattern | CHARACTERS ..."""
    data = _text(field)
    counts = [0] * len(phrases)
    for i, _, _ in _scan(data, phrases):
        counts[i] += 1
    for ph, c in zip(phrases, counts):
        move(int(ph.counter.value) + c, ph.counter)


def inspect_replacing(field: FieldRef, phrases: list[Phrase]) -> None:
    """INSPECT field REPLACING {ALL|LEADING|FIRST} pattern BY repl | CHARACTERS BY c ..."""
    data = bytearray(field.raw)
    for i, pos, n in list(_scan(bytes(data), phrases)):
        by = _text(phrases[i].by)
        if len(by) != n:
            raise ValueError("REPLACING operands must have equal length")
        data[pos:pos + n] = by
    field.set_raw(bytes(data))


def inspect_converting(field: FieldRef, from_chars, to_chars, before=None, after=None) -> None:
    """INSPECT field CONVERTING from TO to [BEFORE|AFTER INITIAL x]."""
    data = bytearray(field.raw)
    f, t = _text(from_chars), _text(to_chars)
    if len(f) != len(t):
        raise ValueError("CONVERTING operands must have equal length")
    table = {}
    for a, b in zip(f, t):
        table.setdefault(a, b)  # first occurrence wins
    s, e = _region(bytes(data), Phrase("CHARACTERS", before=before, after=after))
    for k in range(s, e):
        data[k] = table.get(data[k], data[k])
    field.set_raw(bytes(data))

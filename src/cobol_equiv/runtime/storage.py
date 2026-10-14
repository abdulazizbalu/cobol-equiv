"""Record layouts backed by a byte area.

A COBOL data description is written as nested Python calls:

    ws = Storage("WS", [
        Num("AMOUNT", "S9(5)V99", usage=COMP3),
        Group("IN-DATE", [Num("YYYY", "9(4)"), Num("MM", "99"), Num("DD", "99")]),
        Num("IN-DATE-N", "9(8)", redefines="IN-DATE"),
        Group("ENTRY", [Alnum("CODE", "X(3)"), Num("QTY", "9(3)")], occurs=10),
    ])

    ws["AMOUNT"]            -> FieldRef
    ws.f("CODE", 3)         -> FieldRef for CODE(3) (1-based subscripts,
                               outermost OCCURS first)

Every item lives at a fixed offset of one bytearray, so REDEFINES, group
moves and record I/O behave byte-for-byte like COBOL storage.

Initial state follows GnuCOBOL's default for WORKING-STORAGE without VALUE
clauses: alphanumeric items are spaces, numeric items zero (in their USAGE),
numeric-edited items hold the edited form of zero. VALUE clauses are applied
afterwards with MOVE semantics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Iterator

from . import encoding as enc
from .pic import ALPHABETIC, ALPHANUMERIC, NUMERIC, NUMERIC_EDITED, Pic, parse_pic

GROUP = "group"


# ---- definitions ---------------------------------------------------------

@dataclass
class Item:
    name: str
    pic: Pic | None = None
    usage: str = enc.DISPLAY
    value: Any = None
    occurs: int | None = None
    redefines: str | None = None
    children: list["Item"] = field(default_factory=list)

    @property
    def category(self) -> str:
        return GROUP if self.pic is None else self.pic.category

    def elem_size(self) -> int:
        if self.pic is None:
            sizes: dict[str, int] = {}
            total = 0
            for c in self.children:
                sz = c.elem_size() * (c.occurs or 1)
                if c.redefines:
                    base = sizes[c.redefines]
                    if sz > base:
                        raise ValueError(f"{c.name} REDEFINES {c.redefines} but is larger")
                    continue
                sizes[c.name] = sz
                total += sz
            return total
        if self.pic.category != NUMERIC or self.usage == enc.DISPLAY:
            return self.pic.size
        if self.usage == enc.COMP3:
            return enc.packed_size(self.pic.digits)
        return enc.binary_size(self.pic.digits)


def Num(name, pic, usage=enc.DISPLAY, value=None, occurs=None, redefines=None) -> Item:
    p = parse_pic(pic)
    if p.category != NUMERIC:
        raise ValueError(f"{name}: {pic!r} is not a numeric PICTURE")
    if usage not in enc.NUMERIC_USAGES:
        raise ValueError(f"{name}: unsupported USAGE {usage!r}")
    return Item(name, p, usage, value, occurs, redefines)


def Alnum(name, pic, value=None, occurs=None, redefines=None) -> Item:
    p = parse_pic(pic)
    if p.category not in (ALPHANUMERIC, ALPHABETIC):
        raise ValueError(f"{name}: {pic!r} is not an alphanumeric PICTURE")
    return Item(name, p, enc.DISPLAY, value, occurs, redefines)


def Edited(name, pic, value=None, occurs=None, redefines=None) -> Item:
    p = parse_pic(pic)
    if p.category != NUMERIC_EDITED:
        raise ValueError(f"{name}: {pic!r} is not a numeric-edited PICTURE")
    return Item(name, p, enc.DISPLAY, value, occurs, redefines)


def Filler(pic, value=None) -> Item:
    """Unnamed USAGE DISPLAY item (any category), e.g. Filler("X(3)", " - ")."""
    return Item("FILLER", parse_pic(pic), enc.DISPLAY, value)


def Group(name, children, occurs=None, redefines=None) -> Item:
    return Item(name, None, enc.DISPLAY, None, occurs, redefines, list(children))


# ---- compiled layout -----------------------------------------------------

@dataclass
class Placed:
    item: Item
    offset: int  # offset of the first occurrence
    strides: tuple[tuple[int, int], ...]  # (stride, count) for each enclosing OCCURS incl. own
    size: int  # size of one occurrence


class Storage:
    def __init__(self, name: str, items: list[Item], area: bytearray | None = None):
        self.name = name
        self.root = Group(name, items)
        self.size = self.root.elem_size()
        self.area = area if area is not None else bytearray(self.size)
        if len(self.area) != self.size:
            raise ValueError("area size does not match layout")
        self.placed: dict[str, Placed] = {}
        self.order: list[Placed] = []
        self._place(self.root, 0, ())
        if area is None:  # a supplied area (e.g. a record just read) keeps its bytes
            self.initialize_all()

    def _place(self, item: Item, offset: int, strides: tuple) -> None:
        size = item.elem_size()
        own = strides + ((size, item.occurs),) if item.occurs else strides
        p = Placed(item, offset, own, size)
        if item is not self.root:
            if item.name != "FILLER":
                if item.name in self.placed:
                    raise ValueError(f"duplicate data name {item.name}")
                self.placed[item.name] = p
            self.order.append(p)
        local: dict[str, int] = {}
        pos = offset
        for c in item.children:
            if c.redefines:
                cpos = local[c.redefines]
            else:
                cpos = pos
                local[c.name] = cpos
                pos += c.elem_size() * (c.occurs or 1)
            self._place(c, cpos, own)

    # -- access --
    def f(self, name: str, *subs: int) -> "FieldRef":
        p = self.placed[name]
        if len(subs) != len(p.strides):
            raise IndexError(f"{name} needs {len(p.strides)} subscript(s), got {len(subs)}")
        off = p.offset
        for s, (stride, count) in zip(subs, p.strides):
            if not 1 <= s <= count:
                raise IndexError(f"subscript {s} out of range 1..{count} for {name}")
            off += (s - 1) * stride
        return FieldRef(self.area, off, p.size, p.item, name)

    def __getitem__(self, name: str) -> "FieldRef":
        return self.f(name)

    def record(self) -> "FieldRef":
        return FieldRef(self.area, 0, self.size, self.root, self.name)

    def occurrences(self, placed: Placed) -> Iterator[int]:
        offs = [placed.offset]
        for stride, count in placed.strides:
            offs = [o + i * stride for o in offs for i in range(count)]
        return iter(offs)

    def initialize_all(self) -> None:
        """Default initialisation, then VALUE clauses (redefining items skipped)."""
        from .move import apply_value, set_initial

        skip_under: list[tuple[int, int]] = []
        for p in self.order:
            if p.item.redefines:
                for off in self.occurrences(p):
                    skip_under.append((off, off + p.size))
                continue
            if p.item.pic is None:
                continue
            for off in self.occurrences(p):
                if any(a <= off < b for a, b in skip_under):
                    continue
                ref = FieldRef(self.area, off, p.size, p.item, p.item.name)
                set_initial(ref)
                if p.item.value is not None:
                    apply_value(p.item.value, ref)


class FieldRef:
    """One item (elementary or group) at a fixed position in a byte area."""

    __slots__ = ("area", "offset", "size", "item", "name")

    def __init__(self, area: bytearray, offset: int, size: int, item: Item, name: str):
        self.area = area
        self.offset = offset
        self.size = size
        self.item = item
        self.name = name

    def __repr__(self) -> str:
        return f"FieldRef({self.name}, off={self.offset}, raw={self.raw!r})"

    @property
    def pic(self) -> Pic | None:
        return self.item.pic

    @property
    def usage(self) -> str:
        return self.item.usage

    @property
    def category(self) -> str:
        return self.item.category

    @property
    def raw(self) -> bytes:
        return bytes(self.area[self.offset:self.offset + self.size])

    def set_raw(self, data: bytes) -> None:
        if len(data) != self.size:
            raise ValueError(f"{self.name}: expected {self.size} bytes, got {len(data)}")
        self.area[self.offset:self.offset + self.size] = data

    def child(self, name: str) -> "FieldRef":
        """Child item by name, for groups (first occurrence of OCCURS children only)."""
        off = self.offset
        for c, coff in _child_offsets(self.item):
            if c.name == name:
                return FieldRef(self.area, off + coff, c.elem_size(), c, name)
        raise KeyError(name)

    # -- numeric view --
    def sign_mag(self) -> tuple[bool, int]:
        """(negative, magnitude in units of 10**-scale). Negative zero is kept."""
        p = self.pic
        if p is None or p.category != NUMERIC:
            raise TypeError(f"{self.name} is not numeric")
        raw = self.raw
        u = self.usage
        if u == enc.DISPLAY:
            return enc.decode_display(raw, p.signed)
        if u == enc.COMP3:
            neg, mag = enc.decode_packed(raw)
            return (neg and p.signed), mag
        v = enc.decode_binary(raw, p.signed, u == enc.COMP5)
        return v < 0, abs(v)

    def to_cobdec(self):
        from .cobdec import CobDecimal

        neg, mag = self.sign_mag()
        return CobDecimal(-mag if neg else mag, self.pic.scale)

    @property
    def value(self) -> Decimal:
        if self.category == NUMERIC:
            return self.to_cobdec().to_decimal()
        raise TypeError(f"{self.name} is not numeric; use .raw or .text")

    @property
    def text(self) -> str:
        return self.raw.decode("latin-1")

    def __int__(self) -> int:
        return int(self.value)


def _child_offsets(item: Item):
    local: dict[str, int] = {}
    pos = 0
    for c in item.children:
        if c.redefines:
            yield c, local[c.redefines]
            continue
        local[c.name] = pos
        yield c, pos
        pos += c.elem_size() * (c.occurs or 1)


def refmod(f: FieldRef, start: int, length: int | None = None) -> FieldRef:
    """Reference modification `f (start : length)`: an alphanumeric view of
    bytes start .. start + length - 1 (1-based) of the item, sharing its
    storage. Without length, to the end of the item. A start or length that
    leaves the item is refused (GnuCOBOL without runtime checks would read
    or write outside it)."""
    from .errors import Unsupported

    start = int(start)
    if length is None:
        length = f.size - start + 1
    length = int(length)
    if start < 1 or length < 1 or start + length - 1 > f.size:
        raise Unsupported(f"reference modification ({start}:{length}) outside {f.name} ({f.size} bytes)")
    item = Item(f"{f.name}({start}:{length})", parse_pic(f"X({length})"))
    return FieldRef(f.area, f.offset + start - 1, length, item, item.name)

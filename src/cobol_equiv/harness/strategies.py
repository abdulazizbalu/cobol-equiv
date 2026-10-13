"""Hypothesis strategies derived from PICTURE clauses and record layouts.

Numeric items draw from their boundary values (0, 1 unit in the last place,
the maximum, a value ending in 5 for rounding ties) about half of the time,
and uniformly from the full range otherwise; signed items also get negative
values. Alphanumeric items draw printable ASCII without line breaks.

Generated input files are LINE SEQUENTIAL: one record per line, trailing
spaces removed (as GnuCOBOL writes them), so READ's space padding is
exercised too. Records must therefore use USAGE DISPLAY only.
"""

from __future__ import annotations

import string as _string
from decimal import Decimal

from hypothesis import strategies as st

from ..runtime import encoding as enc
from ..runtime.cobdec import scaled_decimal
from ..runtime.move import move
from ..runtime.pic import ALPHABETIC, ALPHANUMERIC, NUMERIC
from ..runtime.storage import FieldRef, Item, Storage, _child_offsets
from .spec import STDIN, InputSpec

ALNUM_CHARS = _string.ascii_uppercase + _string.digits + " -.,/"


def numeric_values(item: Item):
    p = item.pic
    mx = 10**p.digits - 1
    bounds = {0, 1, mx, mx - 1, mx // 2}
    if p.scale:
        bounds |= {5, 10**p.scale, 10**p.scale + 5}
    bounds = sorted(b for b in bounds if 0 <= b <= mx)
    mags = st.one_of(st.sampled_from(bounds), st.integers(0, mx))
    if p.signed:
        vals = st.tuples(mags, st.booleans()).map(lambda t: -t[0] if t[1] else t[0])
    else:
        vals = mags
    return vals.map(lambda v: scaled_decimal(v, p.scale))


def for_item(item: Item):
    p = item.pic
    if p.category == NUMERIC:
        if item.usage != enc.DISPLAY:
            raise ValueError(f"{item.name}: generated LINE SEQUENTIAL records must be USAGE DISPLAY")
        return numeric_values(item)
    if p.category == ALPHABETIC:
        return st.text(alphabet=_string.ascii_uppercase + " ", max_size=p.size)
    if p.category == ALPHANUMERIC:
        return st.text(alphabet=ALNUM_CHARS, max_size=p.size)
    raise ValueError(f"{item.name}: cannot generate {p.category} input")


def elementary_slots(stg: Storage):
    """(item, FieldRef) for every elementary, non-REDEFINES occurrence."""
    def walk(item, base):
        for c, coff in _child_offsets(item):
            if c.redefines:
                continue
            sz = c.elem_size()
            for i in range(c.occurs or 1):
                off = base + coff + i * sz
                if c.pic is None:
                    yield from walk(c, off)
                else:
                    yield c, FieldRef(stg.area, off, sz, c, c.name)

    yield from walk(stg.root, 0)


@st.composite
def record(draw, spec: InputSpec):
    stg = Storage(spec.name, spec.record)
    for item, ref in elementary_slots(stg):
        strat = spec.overrides[item.name] if item.name in spec.overrides else for_item(item)
        v = draw(strat)
        if item.pic.category == NUMERIC and isinstance(v, str):
            v = Decimal(v)  # numeric override given as text
        move(v, ref)
    return stg


@st.composite
def input_file(draw, spec: InputSpec) -> bytes:
    if spec.record_strategy is not None:
        raw = draw(st.lists(spec.record_strategy, min_size=spec.min_records, max_size=spec.max_records))
        recs = [Storage(spec.name, spec.record, bytearray(r)) for r in raw]
    else:
        recs = draw(st.lists(record(spec), min_size=spec.min_records, max_size=spec.max_records))
    if spec.finalize is not None:
        recs = spec.finalize(recs)
    return b"".join(bytes(r.area).rstrip(b" ") + b"\n" for r in recs)


def inputs(specs: list[InputSpec]):
    """Strategy for the harness input dict {STDIN or file name: bytes}."""
    return st.fixed_dictionaries({s.name: input_file(s) for s in specs})


__all__ = ["STDIN", "for_item", "numeric_values", "record", "input_file", "inputs", "elementary_slots"]

"""Hypothesis strategies derived from PICTURE clauses and record layouts.

Numeric items draw, with equal weight, from (a) their boundary values (0,
one unit in the last place, the maximum, values ending in 5), (b) a value
with a randomly chosen number of digits (so long and short values are both
common), and (c) Hypothesis' integer strategy over the full range, which
favours small values. Signed items also get negative values, and signed
DISPLAY items occasionally a negative zero. Alphanumeric items draw printable
ASCII (0x20-0x7E).

Generated input files are LINE SEQUENTIAL by default: one record per line,
trailing spaces removed (as GnuCOBOL writes them), so READ's space padding
is exercised too; such records must use USAGE DISPLAY only. With
organization "record" the records are concatenated at full length and may
use any USAGE.
"""

from __future__ import annotations

import contextlib
import string as _string
from decimal import Decimal

from hypothesis import strategies as st

from ..runtime import encoding as enc
from ..runtime.cobdec import scaled_decimal
from ..runtime.move import move
from ..runtime.pic import ALPHABETIC, ALPHANUMERIC, NUMERIC
from ..runtime.storage import FieldRef, Item, Storage, _child_offsets
from .spec import STDIN, InputSpec

ALNUM_CHARS = "".join(chr(c) for c in range(0x20, 0x7F))


def numeric_values(item: Item):
    p = item.pic
    mx = 10**p.digits - 1
    bounds = {0, 1, mx, mx - 1, mx // 2}
    if p.scale:
        bounds |= {5, 10**p.scale, 10**p.scale + 5}
    bounds = sorted(b for b in bounds if 0 <= b <= mx)
    by_length = st.integers(1, p.digits).flatmap(lambda k: st.integers(10 ** (k - 1), 10**k - 1))
    mags = st.one_of(st.sampled_from(bounds), by_length, st.integers(0, mx))
    if p.signed:
        vals = st.tuples(mags, st.booleans()).map(lambda t: -t[0] if t[1] else t[0])
    else:
        vals = mags
    return vals.map(lambda v: scaled_decimal(v, p.scale))


def for_item(item: Item, any_usage: bool = False):
    p = item.pic
    if p.category == NUMERIC:
        if item.usage != enc.DISPLAY and not any_usage:
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
        strat = (spec.overrides[item.name] if item.name in spec.overrides
                 else for_item(item, spec.organization == "record"))
        v = draw(strat)
        if item.pic.category == NUMERIC and isinstance(v, str):
            v = Decimal(v)  # numeric override given as text
        move(v, ref)
        p = item.pic
        if (p.category == NUMERIC and p.signed and item.usage == enc.DISPLAY
                and item.name not in spec.overrides and v == 0 and draw(st.integers(0, 3)) == 0):
            ref.set_raw(enc.encode_display(True, 0, p.digits, True))  # negative zero
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
    return file_bytes(spec, recs)


def file_bytes(spec: InputSpec, recs: list) -> bytes:
    if spec.organization == "record":
        return b"".join(bytes(r.area) for r in recs)
    if spec.organization != "line":
        raise ValueError(f"{spec.name}: unknown organization {spec.organization!r}")
    return b"".join(bytes(r.area).rstrip(b" ") + b"\n" for r in recs)


def inputs(specs: list[InputSpec]):
    """Strategy for the harness input dict {STDIN or file name: bytes}."""
    return st.fixed_dictionaries({s.name: input_file(s) for s in specs})


__all__ = ["STDIN", "for_item", "numeric_values", "record", "input_file", "inputs", "elementary_slots"]


@contextlib.contextmanager
def no_local_constants():
    """Hypothesis (since 6.131) mixes literal constants found in the imported
    modules of the project into generated values, so generated inputs would
    depend on which modules happen to be loaded, including the translation
    or mutant under test. Generation turns this off, so that the inputs
    depend only on the spec and the seed. Uses a private name of Hypothesis
    (6.169.0 is pinned in requirements-repro.txt); with a version that lacks
    it, generation runs unchanged."""
    from hypothesis.internal.conjecture import providers

    if not hasattr(providers, "_get_local_constants"):
        yield
        return
    saved = providers._get_local_constants
    providers.CONSTANTS_CACHE.cache.clear()
    providers._get_local_constants = providers.Constants
    try:
        yield
    finally:
        providers._get_local_constants = saved
        providers.CONSTANTS_CACHE.cache.clear()

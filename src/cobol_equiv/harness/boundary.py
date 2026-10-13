"""General boundary vectors, derived from PICTURE clauses only.

For every input file of a program spec this builds sequential files (in
the spec's organization) whose records take boundary values item by item. The values depend only on
each elementary item's PICTURE and USAGE; nothing here looks at mutants,
reference translations, spec overrides or the program's logic, so the set is
the same for any translation of the same record layout.

Numeric item with D digits and S decimal places (values in units of the last
decimal place, 'ulp'):

    zero; 1 ulp; the maximum 10**D - 1 and one less; the smallest value with
    D digits (10**(D-1)); truncation boundaries 10**k - 1 and 10**k for
    0 < k < D; rounding ties 5 * 10**k ulps (0.05, 0.5, 5, ... for S = 2);
    for signed items the negative of each, and a negative zero for signed
    USAGE DISPLAY items.

Alphanumeric item of length N:

    spaces; one character; N characters of 'A', '9', '0' and '~'; a value
    with a leading space.

Records: a base record (every item 1 ulp or 'A'), then for each item and
each of its boundary values a record that differs from the base in that item
only, then 'diagonal' records where every item takes its i-th boundary value
at once. Records are split into files of at most the spec's max_records
(at least one record per file), plus one empty file. The spec's `finalize`
(e.g. sorting for a control break) is applied to each file, because it
describes a property every input file has, not a value choice.
"""

from __future__ import annotations

from ..runtime import encoding as enc
from ..runtime.cobdec import scaled_decimal
from ..runtime.move import move
from ..runtime.pic import NUMERIC
from ..runtime.storage import Item, Storage
from .spec import InputSpec
from .strategies import elementary_slots, file_bytes

NEG_ZERO = "negative zero"


def numeric_boundaries(item: Item) -> list:
    p = item.pic
    d = p.digits
    mx = 10**d - 1
    mags = {0, 1, mx, mx - 1, 10 ** (d - 1)}
    for k in range(1, d):
        mags |= {10**k - 1, 10**k}
    for k in range(d):
        mags.add(5 * 10**k)
    mags = sorted(m for m in mags if 0 <= m <= mx)
    vals = [scaled_decimal(m, p.scale) for m in mags]
    if p.signed:
        vals += [v.copy_negate() for v in vals if v]
        if item.usage == enc.DISPLAY:
            vals.append(NEG_ZERO)
    return vals


def alnum_boundaries(item: Item) -> list[str]:
    n = item.pic.size
    vals = ["", "A", "A" * n, "9" * n, "0" * n, "~" * n, " " + "A" * (n - 1)]
    out = []
    for v in vals:
        if v not in out:
            out.append(v)
    return out


def boundaries(item: Item) -> list:
    return numeric_boundaries(item) if item.pic.category == NUMERIC else alnum_boundaries(item)


def _base(item: Item):
    return scaled_decimal(1, item.pic.scale) if item.pic.category == NUMERIC else "A"


def _store(ref, item, value) -> None:
    if value == NEG_ZERO:
        ref.set_raw(enc.encode_display(True, 0, item.pic.digits, True))
    else:
        move(value, ref)


def boundary_records(spec: InputSpec) -> list[Storage]:
    template = Storage(spec.name, spec.record)
    slots = list(elementary_slots(template))
    values = [boundaries(item) for item, _ in slots]

    def make(choice: dict[int, object]) -> Storage:
        st = Storage(spec.name, spec.record)
        for k, ((item, ref), _) in enumerate(zip(elementary_slots(st), values)):
            _store(ref, item, choice.get(k, _base(item)))
        return st

    recs = [make({})]
    for k, vals in enumerate(values):
        for v in vals:
            recs.append(make({k: v}))
    width = max((len(v) for v in values), default=0)
    for i in range(width):
        recs.append(make({k: vals[i % len(vals)] for k, vals in enumerate(values)}))
    return recs


def boundary_files(spec: InputSpec) -> list[bytes]:
    recs = boundary_records(spec)
    size = max(1, spec.max_records)
    files = [b""]
    for i in range(0, len(recs), size):
        chunk = recs[i:i + size]
        if spec.finalize is not None:
            chunk = spec.finalize(chunk)
        files.append(file_bytes(spec, chunk))
    return files


def boundary_vectors(inputs: list[InputSpec]) -> list[dict[str, bytes]]:
    """Input dicts {file name: content}. With several inputs, the k-th file
    of each is combined (shorter lists repeat their empty file)."""
    per = {s.name: boundary_files(s) for s in inputs}
    n = max((len(v) for v in per.values()), default=0)
    return [{name: (files[i] if i < len(files) else b"") for name, files in per.items()}
            for i in range(n)]

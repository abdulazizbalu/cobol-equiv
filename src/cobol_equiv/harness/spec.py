"""Program specifications and the IO contract for translations.

IO contract
-----------
A Python translation of a COBOL program is a module that defines

    def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
        ...
        return stdout_bytes, {"OUT.DAT": output_bytes, ...}

`input_files` maps the file names the COBOL program ASSIGNs to their full
contents. The translation returns everything the COBOL program would write
to stdout and the full contents of every output file. The translation must
not read the clock, random sources, the network or the file system.

ProgramSpec
-----------
Describes one COBOL program for the harness: where the source is, which
input files (or stdin) it consumes and how to generate them, which output
files to compare, record layouts used to report differences by field name,
and fixed regression vectors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from ..runtime.storage import Item

STDIN = "<stdin>"


def make_records(items: list[Item], rows: list[dict]) -> bytes:
    """LINE SEQUENTIAL file content built with MOVE semantics, for writing
    regression vectors without counting columns by hand. Numeric values may
    be given as text ("-12.50"); they are converted to Decimal."""
    from decimal import Decimal

    from ..runtime.move import move
    from ..runtime.pic import NUMERIC
    from ..runtime.storage import Storage

    out = bytearray()
    for row in rows:
        st = Storage("RECORD", items)
        for name, v in row.items():
            f = st[name]
            if f.category == NUMERIC and isinstance(v, str):
                v = Decimal(v)
            move(v, f)
        out += bytes(st.area).rstrip(b" ") + b"\n"
    return bytes(out)
STDOUT = "<stdout>"


@dataclass
class InputSpec:
    """A sequential input (a file, or STDIN) made of fixed-layout records.

    record: data items of one record (as for Storage).
    min_records / max_records: how many records generated inputs contain.
    overrides: data name -> Hypothesis strategy producing the value for that
        item (int/Decimal for numeric, str for alphanumeric). Use it when
        the program expects a narrower domain than the PICTURE allows (codes,
        valid dates).
    finalize: optional function(list of Storage records) -> list of Storage
        records, e.g. to sort records for a control-break program.
    record_strategy: optional Hypothesis strategy producing a whole record as
        bytes, for layouts that need consistency between fields (REDEFINES
        variants selected by a type code). Replaces the per-item generation.
    organization: "line" (LINE SEQUENTIAL: one record per line, trailing
        spaces removed) or "record" (ORGANIZATION SEQUENTIAL: full-length
        records concatenated, so non-DISPLAY usages such as COMP-3 work).
    """
    name: str
    record: list[Item]
    min_records: int = 0
    max_records: int = 20
    overrides: dict = field(default_factory=dict)
    finalize: Callable[[list], list] | None = None
    record_strategy: object = None
    organization: str = "line"


@dataclass
class OutputLayout:
    """Field layout of output lines, for human-readable difference reports.

    select(line: bytes) -> list[(name, start, length)] or None.
    record_length: for fixed-length record files (ORGANIZATION SEQUENTIAL),
        compare record by record instead of line by line.
    """
    select: Callable[[bytes], list[tuple[str, int, int]] | None]
    record_length: int | None = None


@dataclass
class ProgramSpec:
    name: str
    area: str
    source: Path
    inputs: list[InputSpec] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)  # output file names
    layouts: dict[str, OutputLayout] = field(default_factory=dict)  # STDOUT or file name
    vectors: list[dict[str, bytes]] = field(default_factory=list)  # name -> content
    timeout: float = 10.0
    free_format: bool = False  # compile with cobc -free

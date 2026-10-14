"""Track R program (corpus/tables), written for this repository.

Override and its reason: IT-CODE from ten readable codes, so that codes
repeat and the eight-entry table overflows. This override predates the
benchmark protocol and is kept unchanged.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.compare import columns
from cobol_equiv.harness.spec import STDOUT, InputSpec, OutputLayout, ProgramSpec
from cobol_equiv.runtime import Alnum, Num

HERE = Path(__file__).parent

RECORD = [Alnum("IT-CODE", "X(3)"), Num("IT-QTY", "9(3)"), Num("IT-PRICE", "9(3)V99")]
LINE = columns(("WL-RANK", 2), ("FILLER", 1), ("WL-CODE", 3), ("FILLER", 1), ("WL-QTY", 6),
               ("FILLER", 1), ("WL-AMT", 10))
CODES = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG", "HHH", "III", "JJJ"]


def _stdout(line: bytes):
    return None if line.startswith((b"ITEMS", b"TABLE")) else LINE


SPEC = ProgramSpec(
    name="tables",
    area="OCCURS tables, SEARCH, PERFORM VARYING",
    source=HERE / "program.cob",
    inputs=[InputSpec("ITEMS.DAT", RECORD, 0, 30, overrides={
        "IT-CODE": st.sampled_from(CODES),
    })],
    layouts={STDOUT: OutputLayout(_stdout)},
    vectors=[
        {"ITEMS.DAT": b""},
        # code, qty 9(3), price 9(3)V99
        {"ITEMS.DAT": b"AAA00100150\nBBB00200100\nAAA00300050\nCCC00100300\n"},
        # equal amounts keep input order; nine codes overflow the 8-entry table
        {"ITEMS.DAT": b"AAA00100100\nBBB00100100\nCCC00200050\nDDD00100001\nEEE00100001\n"
                      b"FFF00100001\nGGG00100001\nHHH00100001\nIII00100001\nAAA00100001\n"},
        # amount accumulation beyond 9(6)V99 is truncated on the left
        {"ITEMS.DAT": b"AAA99999999\n" * 12},
    ],
)

"""Track R program (corpus/ctlbreak), written for this repository.

Overrides and their reasons: SL-REGION and SL-BRANCH from short lists of
readable codes, so that control breaks occur. finalize sorts the records by
the control keys (the program's input is sorted, as for any control-break
report). These overrides predate the benchmark protocol and are kept
unchanged.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.compare import columns
from cobol_equiv.harness.spec import InputSpec, OutputLayout, ProgramSpec
from cobol_equiv.runtime import Alnum, Num

HERE = Path(__file__).parent

RECORD = [Alnum("SL-REGION", "X(2)"), Alnum("SL-BRANCH", "X(3)"), Num("SL-AMOUNT", "S9(5)V99")]
BRANCH = columns(("FILLER", 4), ("BL-REGION", 2), ("FILLER", 1), ("BL-BRANCH", 3), ("FILLER", 1),
                 ("BL-COUNT", 4), ("FILLER", 1), ("BL-TOTAL", 14))
REGION = columns(("FILLER", 7), ("RL-REGION", 2), ("FILLER", 6), ("RL-TOTAL", 14))
GRAND = columns(("FILLER", 6), ("GL-COUNT", 6), ("FILLER", 1), ("GL-TOTAL", 16))


def _report(line: bytes):
    if line.startswith(b"REGION"):
        return REGION
    if line.startswith(b"GRAND"):
        return GRAND
    if line.startswith(b"    "):
        return BRANCH
    return None


def _sort(recs):
    return sorted(recs, key=lambda r: bytes(r.area[:5]))


SPEC = ProgramSpec(
    name="ctlbreak",
    area="sequential file with control break",
    source=HERE / "program.cob",
    inputs=[InputSpec("SALES.DAT", RECORD, 0, 30, finalize=_sort, overrides={
        "SL-REGION": st.sampled_from(["EA", "NO", "SO", "WE"]),
        "SL-BRANCH": st.sampled_from(["B01", "B02", "B10"]),
    })],
    outputs=["REPORT.DAT"],
    layouts={"REPORT.DAT": OutputLayout(_report)},
    vectors=[
        {"SALES.DAT": b""},
        # region, branch, amount S9(5)V99 (overpunch sign)
        {"SALES.DAT": b"EAB010001000\nEAB01000050u\nEAB020010000\nNOB019999999\nNOB019999999\n"
                      b"SOB10000000p\nWEB01999999y\n"},
        {"SALES.DAT": b"EAB010000001\n"},
    ],
)

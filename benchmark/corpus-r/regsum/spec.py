"""Track R program written for this repository.

Input SALES.DAT, LINE SEQUENTIAL, sorted by region (stated in the program
header; finalize sorts the generated records by SL-REGION, keeping their
order within a region). Overrides: SL-REGION from four readable region
codes; SL-MONTH 0 .. 13 (domain stated by the program's validation, 1-12,
plus one invalid value on each side).
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import InputSpec, ProgramSpec, make_records
from cobol_equiv.runtime import Alnum, Num

HERE = Path(__file__).parent

RECORD = [Alnum("SL-REGION", "X(2)"), Num("SL-MONTH", "99"), Num("SL-AMOUNT", "S9(5)V99")]


def _sort(recs):
    return sorted(recs, key=lambda r: bytes(r.area[:2]))


SPEC = ProgramSpec(
    name="regsum",
    area="INITIALIZE of a multi-level group with OCCURS, control break",
    source=HERE / "program.cob",
    inputs=[InputSpec("SALES.DAT", RECORD, 0, 30, finalize=_sort, overrides={
        "SL-REGION": st.sampled_from(["EA", "NO", "SO", "WE"]),
        "SL-MONTH": st.integers(0, 13),
    })],
    vectors=[
        {"SALES.DAT": b""},
        {"SALES.DAT": make_records(RECORD, [
            {"SL-REGION": "EA", "SL-MONTH": 1, "SL-AMOUNT": "100.00"},
            {"SL-REGION": "EA", "SL-MONTH": 3, "SL-AMOUNT": "-100.00"},
            {"SL-REGION": "EA", "SL-MONTH": 13, "SL-AMOUNT": "5.00"},
            {"SL-REGION": "NO", "SL-MONTH": 12, "SL-AMOUNT": "99999.99"},
            {"SL-REGION": "NO", "SL-MONTH": 12, "SL-AMOUNT": "-0.01"},
            {"SL-REGION": "SO", "SL-MONTH": 0, "SL-AMOUNT": "1.00"},
        ])},
    ],
)

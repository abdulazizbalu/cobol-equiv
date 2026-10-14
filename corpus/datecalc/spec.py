"""Track R program (corpus/datecalc), written for this repository.

Overrides and their reasons:
- DT-FROM, DT-TO: half valid calendar dates 1601-01-01 .. 9999-12-31 (the
  range the program's date validation accepts), a quarter edge dates
  (leap days, invalid months and days), a quarter the full PICTURE.
- DT-OFFSET: values at the edges of the PICTURE plus the full PICTURE
  range (not narrowed).
These overrides predate the benchmark protocol and are kept unchanged.
"""

import datetime
from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.compare import columns
from cobol_equiv.harness.spec import STDOUT, InputSpec, OutputLayout, ProgramSpec, make_records
from cobol_equiv.runtime import Num

HERE = Path(__file__).parent

RECORD = [Num("DT-FROM", "9(8)"), Num("DT-TO", "9(8)"), Num("DT-OFFSET", "S9(6)")]
LINE = columns(("DT-FROM", 8), ("FILLER", 1), ("DT-TO", 8), ("FILLER", 1), ("WS-DIFF-ED", 8),
               ("FILLER", 1), ("WS-DOW-NAME", 3), ("FILLER", 1), ("WS-RESULT", 8))

valid_dates = st.dates(datetime.date(1601, 1, 1), datetime.date(9999, 12, 31)).map(
    lambda d: int(d.strftime("%Y%m%d")))
edge_dates = st.sampled_from([16010101, 99991231, 20000229, 19000228, 19000229, 21000301,
                              20241231, 20250229, 16001231, 20261301, 20261000, 0])
dates = st.one_of(valid_dates, valid_dates, edge_dates, st.integers(0, 99999999))

SPEC = ProgramSpec(
    name="datecalc",
    area="date arithmetic without the system clock",
    source=HERE / "program.cob",
    inputs=[InputSpec("DATES.DAT", RECORD, 0, 8, overrides={
        "DT-FROM": dates, "DT-TO": dates,
        "DT-OFFSET": st.one_of(st.sampled_from([0, 1, -1, 365, 366, -365, 999999, -999999]),
                               st.integers(-999999, 999999)),
    })],
    layouts={STDOUT: OutputLayout(lambda line: None if b"INVALID" in line else LINE)},
    vectors=[
        {"DATES.DAT": b""},
        {"DATES.DAT": make_records(RECORD, [
            {"DT-FROM": 16010101, "DT-TO": 20261013, "DT-OFFSET": 0},
            {"DT-FROM": 20000229, "DT-TO": 20000301, "DT-OFFSET": 365},
            {"DT-FROM": 20250229, "DT-TO": 20250101, "DT-OFFSET": 0},
            {"DT-FROM": 99991231, "DT-TO": 16010101, "DT-OFFSET": 1},
            {"DT-FROM": 20261013, "DT-TO": 20261013, "DT-OFFSET": -1},
            {"DT-FROM": 19000228, "DT-TO": 19000301, "DT-OFFSET": 1},
            {"DT-FROM": 16010101, "DT-TO": 16010101, "DT-OFFSET": -1},
            {"DT-FROM": 20240229, "DT-TO": 21000228, "DT-OFFSET": 27759},
        ])},
    ],
)

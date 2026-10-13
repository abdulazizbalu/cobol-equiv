"""Track R program written for this repository.

Input CELLS.DAT, LINE SEQUENTIAL. Overrides: CL-ROW and CL-COL 0 .. 6
(domains stated by the program's validation, 1-4 and 1-5, plus invalid
values); CL-OP from "=", "+", "*" and "?" (the operations the program
accepts, plus one it rejects). CL-VAL uses its full PICTURE domain.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import InputSpec, ProgramSpec, make_records
from cobol_equiv.runtime import Alnum, Num

HERE = Path(__file__).parent

RECORD = [Num("CL-ROW", "9"), Num("CL-COL", "9"), Alnum("CL-OP", "X"), Num("CL-VAL", "S9(3)")]

SPEC = ProgramSpec(
    name="matrix",
    area="two-level OCCURS, PERFORM VARYING AFTER, nested PERFORM",
    source=HERE / "program.cob",
    inputs=[InputSpec("CELLS.DAT", RECORD, 0, 30, overrides={
        "CL-ROW": st.integers(0, 6),
        "CL-COL": st.integers(0, 6),
        "CL-OP": st.sampled_from(["=", "+", "*", "?"]),
    })],
    vectors=[
        {"CELLS.DAT": b""},
        {"CELLS.DAT": make_records(RECORD, [
            {"CL-ROW": 1, "CL-COL": 1, "CL-OP": "=", "CL-VAL": 100},
            {"CL-ROW": 1, "CL-COL": 1, "CL-OP": "+", "CL-VAL": -50},
            {"CL-ROW": 4, "CL-COL": 5, "CL-OP": "*", "CL-VAL": 999},
            {"CL-ROW": 4, "CL-COL": 5, "CL-OP": "=", "CL-VAL": 999},
            {"CL-ROW": 4, "CL-COL": 5, "CL-OP": "*", "CL-VAL": 999},
            {"CL-ROW": 2, "CL-COL": 3, "CL-OP": "*", "CL-VAL": 2},
            {"CL-ROW": 9, "CL-COL": 9, "CL-OP": "=", "CL-VAL": 1},
            {"CL-ROW": 1, "CL-COL": 2, "CL-OP": "?", "CL-VAL": 1},
        ])},
    ],
)

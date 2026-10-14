"""Track R program written for this repository.

Input LOANS.DAT, LINE SEQUENTIAL. Overrides: LN-ID from readable IDs;
LN-YEARS 0 .. 41 and LN-FREQ 0 .. 5 (domains stated by the program's
validation, 1-40 and 1-4, plus one invalid value on each side).
Principal and rate use their full PICTURE domains.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import InputSpec, ProgramSpec, make_records
from cobol_equiv.runtime import Alnum, Num

HERE = Path(__file__).parent

RECORD = [Alnum("LN-ID", "X(4)"), Num("LN-PRINCIPAL", "9(7)V99"), Num("LN-RATE", "99V999"),
          Num("LN-YEARS", "99"), Num("LN-FREQ", "9")]

SPEC = ProgramSpec(
    name="interest",
    area="COMPUTE with several operators, parentheses, unary minus, ROUNDED, ON SIZE ERROR",
    source=HERE / "program.cob",
    inputs=[InputSpec("LOANS.DAT", RECORD, 0, 10, overrides={
        "LN-ID": st.sampled_from(["L001", "L002", "L003", "L004"]),
        "LN-YEARS": st.integers(0, 41),
        "LN-FREQ": st.integers(0, 5),
    })],
    vectors=[
        {"LOANS.DAT": b""},
        {"LOANS.DAT": make_records(RECORD, [
            {"LN-ID": "L001", "LN-PRINCIPAL": "1000.00", "LN-RATE": "5.000", "LN-YEARS": 10, "LN-FREQ": 1},
            {"LN-ID": "L002", "LN-PRINCIPAL": "9999999.99", "LN-RATE": "99.999", "LN-YEARS": 40,
             "LN-FREQ": 4},
            {"LN-ID": "L003", "LN-PRINCIPAL": "0.00", "LN-RATE": "0.000", "LN-YEARS": 0, "LN-FREQ": 1},
            {"LN-ID": "L004", "LN-PRINCIPAL": "10000.00", "LN-RATE": "12.345", "LN-YEARS": 40,
             "LN-FREQ": 3},
            {"LN-ID": "L001", "LN-PRINCIPAL": "1.00", "LN-RATE": "0.001", "LN-YEARS": 1, "LN-FREQ": 9},
        ])},
    ],
)

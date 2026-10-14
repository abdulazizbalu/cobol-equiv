"""Track R program written for this repository.

Input CUST.DAT, LINE SEQUENTIAL; output CUSTLIST.DAT. Overrides: CU-MM
0 .. 13 (domain stated by the program's validation, 1-12, plus one
invalid value on each side). All other items use their full PICTURE
domains.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import InputSpec, ProgramSpec, make_records
from cobol_equiv.runtime import Alnum, Group, Num

HERE = Path(__file__).parent

RECORD = [
    Num("CU-ID", "9(5)"),
    Group("CU-NAME", [Alnum("CU-LAST", "X(10)"), Alnum("CU-FIRST", "X(8)")]),
    Group("CU-ADDR", [
        Group("CU-STREET", [Num("CU-HOUSE", "9(4)"), Alnum("CU-ROAD", "X(12)")]),
        Alnum("CU-CITY", "X(10)"),
    ]),
    Group("CU-OPENED", [Num("CU-YYYY", "9(4)"), Num("CU-MM", "99"), Num("CU-DD", "99")]),
    Num("CU-BAL", "S9(5)V99"),
]

SPEC = ProgramSpec(
    name="custlist",
    area="multi-level groups, MOVE CORRESPONDING, group moves, REDEFINES",
    source=HERE / "program.cob",
    inputs=[InputSpec("CUST.DAT", RECORD, 0, 20, overrides={"CU-MM": st.integers(0, 13)})],
    outputs=["CUSTLIST.DAT"],
    vectors=[
        {"CUST.DAT": b""},
        {"CUST.DAT": make_records(RECORD, [
            {"CU-ID": 42, "CU-LAST": "Smith", "CU-FIRST": "John", "CU-HOUSE": 12, "CU-ROAD": "Main St",
             "CU-CITY": "Tashkent", "CU-YYYY": 2024, "CU-MM": 3, "CU-DD": 15, "CU-BAL": "-12.30"},
            {"CU-ID": 99999, "CU-FIRST": "Ann", "CU-HOUSE": 9999, "CU-YYYY": 1899, "CU-MM": 12,
             "CU-DD": 31, "CU-BAL": "0"},
            {"CU-ID": 0, "CU-LAST": "X", "CU-YYYY": 2000, "CU-MM": 13, "CU-DD": 1, "CU-BAL": "99999.99"},
        ])},
    ],
)

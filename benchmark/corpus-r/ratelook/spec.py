"""Track R program written for this repository.

Input SHIPS.DAT, LINE SEQUENTIAL. Overrides (readable IDs): SH-ZONE comes
from the six zones of the rate table plus two that are not in it, SH-CLASS
from E, S and X (X is not in the table). Weight and quantity use their full
PICTURE domains.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import InputSpec, ProgramSpec, make_records
from cobol_equiv.runtime import Alnum, Num

HERE = Path(__file__).parent

RECORD = [Alnum("SH-ZONE", "X(2)"), Alnum("SH-CLASS", "X"), Num("SH-WEIGHT", "9(3)V9"),
          Num("SH-QTY", "99")]

SPEC = ProgramSpec(
    name="ratelook",
    area="SEARCH ALL with ASCENDING KEY, table loaded by REDEFINES of VALUE data",
    source=HERE / "program.cob",
    inputs=[InputSpec("SHIPS.DAT", RECORD, 0, 30, overrides={
        "SH-ZONE": st.sampled_from(["AA", "BK", "CN", "DE", "FR", "UZ", "AB", "ZZ"]),
        "SH-CLASS": st.sampled_from(["E", "S", "X"]),
    })],
    vectors=[
        {"SHIPS.DAT": b""},
        {"SHIPS.DAT": make_records(RECORD, [
            {"SH-ZONE": "AA", "SH-CLASS": "E", "SH-WEIGHT": "1.0", "SH-QTY": 10},
            {"SH-ZONE": "UZ", "SH-CLASS": "S", "SH-WEIGHT": "999.9", "SH-QTY": 99},
            {"SH-ZONE": "ZZ", "SH-CLASS": "E", "SH-WEIGHT": "1.0", "SH-QTY": 1},
            {"SH-ZONE": "CN", "SH-CLASS": "S", "SH-WEIGHT": "123.4", "SH-QTY": 59},
            {"SH-ZONE": "AA", "SH-CLASS": "S", "SH-WEIGHT": "0.0", "SH-QTY": 0},
        ])},
    ],
)

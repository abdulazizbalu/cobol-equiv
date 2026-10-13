"""Track R program written for this repository.

Input TRANS.DAT, LINE SEQUENTIAL. Overrides (readable IDs): TR-PART from
the eight part numbers of the program's table plus two that are not in it;
TR-CODE from the four codes the program accepts (R, I, +, -) plus X, which
it rejects. TR-QTY uses its full PICTURE domain.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import InputSpec, ProgramSpec, make_records
from cobol_equiv.runtime import Alnum, Num

HERE = Path(__file__).parent

RECORD = [Num("TR-PART", "9(4)"), Alnum("TR-CODE", "X"), Num("TR-QTY", "9(3)")]
PARTS = [1010, 1020, 1110, 2005, 2500, 3300, 4001, 7777, 1000, 9999]

SPEC = ProgramSpec(
    name="stockupd",
    area="SECTIONs, level-88 conditions, SET TO TRUE, SEARCH ALL on a numeric key, INITIALIZE",
    source=HERE / "program.cob",
    inputs=[InputSpec("TRANS.DAT", RECORD, 0, 30, overrides={
        "TR-PART": st.sampled_from(PARTS),
        "TR-CODE": st.sampled_from(["R", "I", "+", "-", "X"]),
    })],
    vectors=[
        {"TRANS.DAT": b""},
        {"TRANS.DAT": make_records(RECORD, [
            {"TR-PART": 1010, "TR-CODE": "R", "TR-QTY": 600},
            {"TR-PART": 1010, "TR-CODE": "I", "TR-QTY": 999},
            {"TR-PART": 9999, "TR-CODE": "R", "TR-QTY": 1},
            {"TR-PART": 2005, "TR-CODE": "I", "TR-QTY": 20},
            {"TR-PART": 2500, "TR-CODE": "+", "TR-QTY": 5},
            {"TR-PART": 2500, "TR-CODE": "-", "TR-QTY": 10},
            {"TR-PART": 4001, "TR-CODE": "X", "TR-QTY": 1},
            {"TR-PART": 7777, "TR-CODE": "I", "TR-QTY": 100},
            {"TR-PART": 7777, "TR-CODE": "-", "TR-QTY": 50},
        ])},
    ],
)

"""Track R program written for this repository.

Input TXNS.DAT, LINE SEQUENTIAL. Override (readable IDs): account numbers
come from a list of seven, so that the five-account table fills up, plus
spaces, which the program rejects. TX-TYPE uses its full PICTURE domain
0-9 (the program accepts 1-3 and reports the others).
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import InputSpec, ProgramSpec, make_records
from cobol_equiv.runtime import Alnum, Num

HERE = Path(__file__).parent

RECORD = [Alnum("TX-ACCT", "X(4)"), Num("TX-TYPE", "9"), Num("TX-AMT", "9(5)V99")]
ACCOUNTS = ["A001", "A002", "B001", "B002", "C001", "C002", "D001", "    "]

SPEC = ProgramSpec(
    name="acctpost",
    area="PERFORM THRU, GO TO, GO TO DEPENDING ON, nested PERFORM",
    source=HERE / "program.cob",
    inputs=[InputSpec("TXNS.DAT", RECORD, 0, 30, overrides={
        "TX-ACCT": st.sampled_from(ACCOUNTS),
    })],
    vectors=[
        {"TXNS.DAT": b""},
        {"TXNS.DAT": make_records(RECORD, [
            {"TX-ACCT": "A001", "TX-TYPE": 1, "TX-AMT": "100.00"},
            {"TX-ACCT": "A001", "TX-TYPE": 2, "TX-AMT": "5.00"},
            {"TX-ACCT": "A001", "TX-TYPE": 3, "TX-AMT": "123.45"},
            {"TX-ACCT": "B001", "TX-TYPE": 2, "TX-AMT": "999.99"},
            {"TX-ACCT": "    ", "TX-TYPE": 1, "TX-AMT": "1.00"},
            {"TX-ACCT": "A001", "TX-TYPE": 9, "TX-AMT": "1.00"},
            {"TX-ACCT": "C001", "TX-TYPE": 1, "TX-AMT": "0.01"},
            {"TX-ACCT": "D001", "TX-TYPE": 1, "TX-AMT": "0.01"},
            {"TX-ACCT": "A002", "TX-TYPE": 1, "TX-AMT": "0.01"},
            {"TX-ACCT": "B002", "TX-TYPE": 1, "TX-AMT": "0.01"},
            {"TX-ACCT": "A001", "TX-TYPE": 3, "TX-AMT": "99999.99"},
        ])},
    ],
)

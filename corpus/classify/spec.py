"""Track R program (corpus/classify), written for this repository.

Overrides and their reasons:
- CU-ID: "C" and three digits (readable IDs).
- CU-TYPE: the codes the program tests (P, B) and others it does not
  (G, H, I, J, K, F, A, space); readable codes.
- CU-AGE, CU-DAYS-LATE: half of the values from the thresholds the program
  compares against, half over 0 .. 120 (age) or the full PICTURE (days
  late). The age range 0 .. 120 narrows the PICTURE (0 .. 999); it is not
  stated by the program.
- CU-BALANCE: half from the thresholds the program compares against, half
  over -99999.99 .. 99999.99, which narrows the PICTURE (S9(7)V99); not
  stated by the program.
These overrides predate the benchmark protocol and are kept unchanged.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.compare import columns
from cobol_equiv.harness.spec import STDOUT, InputSpec, OutputLayout, ProgramSpec
from decimal import Decimal

from cobol_equiv.runtime import Alnum, Num, Storage, move

HERE = Path(__file__).parent

RECORD = [Alnum("CU-ID", "X(4)"), Alnum("CU-TYPE", "X"), Num("CU-AGE", "9(3)"),
          Num("CU-BALANCE", "S9(7)V99"), Num("CU-DAYS-LATE", "9(3)")]
LINE = columns(("CU-ID", 4), ("FILLER", 1), ("WS-CLASS", 7), ("FILLER", 1), ("WS-SEGMENT", 10),
               ("FILLER", 1), ("WS-RISK", 1), ("FILLER", 1), ("WS-AGEBAND", 6))
EDGES = ["-500.01", "-500.00", "-0.01", "0", "1000.00", "1000.01", "10000.00", "10000.01",
         "50000.00", "50000.01"]

def _rec(cid, typ, age, balance, late):
    """One CUST.DAT line; the balance is written with a trailing overpunch sign."""
    st = Storage("R", RECORD)
    move(cid, st["CU-ID"]); move(typ, st["CU-TYPE"]); move(age, st["CU-AGE"])
    move(Decimal(balance), st["CU-BALANCE"]); move(late, st["CU-DAYS-LATE"])
    return bytes(st.area) + b"\n"


SPEC = ProgramSpec(
    name="classify",
    area="EVALUATE and nested IF classification",
    source=HERE / "program.cob",
    inputs=[InputSpec("CUST.DAT", RECORD, 0, 20, overrides={
        "CU-ID": st.from_regex(r"C[0-9]{3}", fullmatch=True),
        "CU-TYPE": st.sampled_from(list("PBGHIJKFA ")),
        "CU-AGE": st.one_of(st.sampled_from([0, 17, 18, 24, 25, 64, 65, 999]), st.integers(0, 120)),
        "CU-DAYS-LATE": st.one_of(st.sampled_from([0, 30, 31, 60, 61, 90, 91]), st.integers(0, 999)),
        "CU-BALANCE": st.one_of(st.sampled_from(EDGES), st.decimals("-99999.99", "99999.99", places=2)),
    })],
    layouts={STDOUT: OutputLayout(lambda line: None if line.startswith(b"CREDIT ") else LINE)},
    vectors=[
        {"CUST.DAT": b""},
        {"CUST.DAT": b"".join(_rec(*r) for r in [
            ("C001", "P", 24, "0001000.00", 0), ("C002", "P", 65, "-0050000.01", 31),
            ("C003", "B", 40, "0050000.01", 61), ("C004", "H", 18, "0001000.00", 91),
            ("C005", "K", 17, "0000010.00", 30), ("C006", "B", 30, "0010000.00", 0),
            ("C007", "P", 64, "-0000500.00", 0), ("C008", "J", 999, "-0000500.01", 999),
        ])},
    ],
)

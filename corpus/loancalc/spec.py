"""Track R program (corpus/loancalc), written for this repository.

Overrides and their reasons:
- LN-ID: "L" and five digits (readable IDs).
- LN-TERM: 0 .. 480 plus the edge values 0, 1, 12, 360; narrows the
  PICTURE (0 .. 999) to keep the amortisation loop short; not stated by
  the program (it rejects only 0).
- LN-RATE: 0 .. 30 plus edge values up to 99.999; narrows the PICTURE for
  realistic rates; not stated by the program.
These overrides predate the benchmark protocol and are kept unchanged.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.compare import columns
from cobol_equiv.harness.spec import STDOUT, InputSpec, OutputLayout, ProgramSpec
from cobol_equiv.runtime import Alnum, Num

HERE = Path(__file__).parent

RECORD = [Alnum("LN-ID", "X(6)"), Num("LN-PRINCIPAL", "9(7)V99"), Num("LN-RATE", "99V999"),
          Num("LN-TERM", "9(3)")]

OUT = columns(("OL-ID", 6), ("FILLER", 1), ("OL-PAYMENT", 13), ("FILLER", 1),
              ("OL-TOTAL-INT", 13), ("FILLER", 1), ("OL-MONTHS", 3), ("FILLER", 1),
              ("OL-FIRST-INT", 12), ("FILLER", 1), ("OL-RESIDUAL", 11))


def _select(line: bytes):
    if b"ERROR" in line or line.startswith(b"LOANS "):
        return None
    return OUT


SPEC = ProgramSpec(
    name="loancalc",
    area="fixed-point interest and loan calculation with ROUNDED",
    source=HERE / "program.cob",
    inputs=[InputSpec("LOANS.DAT", RECORD, 0, 6, overrides={
        "LN-ID": st.from_regex(r"L[0-9]{5}", fullmatch=True),
        "LN-TERM": st.one_of(st.sampled_from([0, 1, 12, 360]), st.integers(0, 480)),
        "LN-RATE": st.one_of(st.sampled_from(["0", "0.001", "5.250", "99.999"]),
                             st.decimals("0", "30", places=3)),
    })],
    layouts={STDOUT: OutputLayout(_select)},
    vectors=[
        {"LOANS.DAT": b""},
        # id, principal 9(7)V99, annual rate % 99V999, term months 9(3)
        {"LOANS.DAT": b"L00001" b"010000000" b"05250" b"360\n"
                      b"L00002" b"000100000" b"00000" b"012\n"
                      b"L00003" b"000000000" b"12000" b"000\n"
                      b"L00004" b"999999999" b"99999" b"001\n"
                      b"L00005" b"999999999" b"99999" b"360\n"
                      b"L00006" b"000000001" b"00001" b"001\n"
                      b"L00007" b"001234567" b"00001" b"999\n"},
    ],
)

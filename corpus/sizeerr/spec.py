from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.compare import columns
from cobol_equiv.harness.spec import STDOUT, InputSpec, OutputLayout, ProgramSpec
from cobol_equiv.runtime import Alnum, Num

HERE = Path(__file__).parent

RECORD = [Alnum("TX-ACCT", "X(4)"), Alnum("TX-OP", "X"), Num("TX-AMOUNT", "S9(5)V99")]
SHOW = columns(("TX-ACCT", 4), ("STATUS", 7), ("TX-OP", 1), ("FILLER", 1), ("WS-ACC", 9),
               ("FILLER", 1), ("WS-RAW", 9), ("FILLER", 1), ("WS-BIN", 5))
QR = columns(("TX-ACCT", 4), ("FILLER", 3), ("WS-QUOT", 6), ("FILLER", 3), ("WS-REM", 9))


def _stdout(line: bytes):
    if line[4:7] == b" Q ":
        return QR
    if line[4:11] in (b" OK    ", b" ERROR "):
        return SHOW
    return None


SPEC = ProgramSpec(
    name="sizeerr",
    area="ON SIZE ERROR handling and truncation",
    source=HERE / "program.cob",
    inputs=[InputSpec("TXN.DAT", RECORD, 0, 25, overrides={
        "TX-ACCT": st.from_regex(r"A[0-9]{3}", fullmatch=True),
        "TX-OP": st.sampled_from(["A", "S", "M", "D", "Q", "X"]),
    })],
    layouts={STDOUT: OutputLayout(_stdout)},
    vectors=[
        {"TXN.DAT": b""},
        # acct, op, amount S9(5)V99 with trailing overpunch sign
        {"TXN.DAT": b"A001A9999999\n"   # +99999.99
                    b"A002A0000001\n"   # +0.01 -> size error on ACC
                    b"A003S000000q\n"   # -0.01 subtracted
                    b"A004M0000200\n"   # * 2.00
                    b"A005D0000000\n"   # / 0 -> size error, RAW unchanged
                    b"A006D0000300\n"   # / 3.00 rounded
                    b"A007Q0000700\n"   # quotient and remainder
                    b"A008Q0000000\n"   # divide by zero
                    b"A009Z0000000\n"},
    ],
)

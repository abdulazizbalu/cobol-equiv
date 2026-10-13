from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.compare import columns
from cobol_equiv.harness.spec import STDOUT, InputSpec, OutputLayout, ProgramSpec
from cobol_equiv.runtime import Alnum, Num

HERE = Path(__file__).parent

RECORD = [
    Alnum("EMP-ID", "X(5)"), Alnum("EMP-NAME", "X(10)"), Num("EMP-HOURS", "9(3)V9"),
    Num("EMP-RATE", "9(3)V99"), Alnum("EMP-DED-CODE", "X"), Num("EMP-ADJUST", "S9(5)V99"),
]

DETAIL = columns(("EMP-ID", 5), ("FILLER", 1), ("EMP-NAME", 10), ("FILLER", 1),
                 ("WS-GROSS", 11), ("FILLER", 1), ("WS-TAX", 11), ("FILLER", 1),
                 ("WS-DED", 9), ("FILLER", 1), ("WS-NET", 11))
PAYOUT = columns(("PAY-ID", 5), ("PAY-GROSS", 5), ("PAY-NET", 5), ("PAY-NET-D", 9), ("PAY-FLAG", 1))


def _stdout(line: bytes):
    return None if line.startswith((b"EMPLOYEES", b"TOTAL", b"NEGATIVE")) else DETAIL


SPEC = ProgramSpec(
    name="payroll",
    area="COMP-3 payroll with signed values",
    source=HERE / "program.cob",
    inputs=[InputSpec("EMPLOYEES.DAT", RECORD, 0, 8, overrides={
        "EMP-ID": st.from_regex(r"E[0-9]{4}", fullmatch=True),
        "EMP-DED-CODE": st.sampled_from(["A", "B", "C", "X", " "]),
        "EMP-HOURS": st.one_of(st.sampled_from(["0", "40", "40.1", "39.9", "999.9"]),
                               st.decimals("0", "80", places=1)),
    })],
    outputs=["PAYOUT.DAT"],
    layouts={STDOUT: OutputLayout(_stdout), "PAYOUT.DAT": OutputLayout(lambda rec: PAYOUT, record_length=25)},
    vectors=[
        {"EMPLOYEES.DAT": b""},
        # id, name X(10), hours 9(3)V9, rate 9(3)V99, code, adjust S9(5)V99 (overpunch)
        {"EMPLOYEES.DAT": b"E0001" b"ADAMS     " b"0400" b"02500" b"A" b"0000000\n"
                          b"E0002" b"BAKER     " b"0455" b"03333" b"B" b"001234u\n"
                          b"E0003" b"CRUZ      " b"0000" b"00000" b"C" b"999999y\n"
                          b"E0004" b"DIAZ      " b"9999" b"99999" b"X" b"9999999\n"
                          b"E0005" b"EVANS     " b"0401" b"01000" b" " b"000000p\n"},
    ],
)

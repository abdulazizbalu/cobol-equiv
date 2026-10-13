from pathlib import Path

from cobol_equiv.harness.compare import columns
from cobol_equiv.harness.spec import InputSpec, OutputLayout, ProgramSpec, make_records
from cobol_equiv.runtime import Alnum, Num

HERE = Path(__file__).parent

RECORD = [Alnum("AM-LABEL", "X(6)"), Num("AM-VALUE", "S9(7)V99"), Num("AM-DATE", "9(6)"),
          Num("AM-QTY", "S9(4)")]
KEYS = ("AM-LABEL", "AM-VALUE", "AM-DATE", "AM-QTY")
LINE1 = columns(("L1-LABEL", 6), ("FILLER", 1), ("L1-A", 11), ("FILLER", 1), ("L1-B", 16),
                ("FILLER", 1), ("L1-C", 14), ("FILLER", 1), ("L1-D", 5), ("FILLER", 1),
                ("L1-E", 8), ("FILLER", 1), ("L1-F", 7))
LINE2 = columns(("FILLER", 7), ("L2-G", 9), ("FILLER", 1), ("L2-H", 7), ("FILLER", 1),
                ("L2-I", 12), ("FILLER", 1), ("L2-J", 6), ("FILLER", 1), ("L2-K", 4))
TOTAL = columns(("FILLER", 7), ("TL-AMOUNT", 17), ("FILLER", 5), ("TL-QTY", 7))


def _select(line: bytes):
    if line.startswith(b"TOTAL  "):
        return TOTAL
    # LINE-2 has its decimal point (L2-G) at index 12; LINE-1 has L1-A's at
    # index 14. The label can be blank, so the leading spaces do not decide.
    if line[12:13] == b".":
        return LINE2
    return LINE1


SPEC = ProgramSpec(
    name="report",
    area="numeric-edited report lines",
    source=HERE / "program.cob",
    inputs=[InputSpec("AMOUNTS.DAT", RECORD, 0, 10)],
    outputs=["REPORT.DAT"],
    layouts={"REPORT.DAT": OutputLayout(_select)},
    vectors=[
        {"AMOUNTS.DAT": b""},
        {"AMOUNTS.DAT": make_records(RECORD, [
            dict(zip(KEYS, r)) for r in [
                ("ZERO", "0", 0, "-0"), ("SMALL", "-0.07", 261013, "1"),
                ("BIG", "9999999.99", 291231, "9999"), ("NEG", "-9999999.99", 10101, "-9999"),
                ("MIXED", "12345.67", 123456, "-121"), ("CENT", "0.01", 991231, "-1"),
            ]])},
    ],
)

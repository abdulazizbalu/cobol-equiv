"""Reference translation of the Rosetta Code "Last Friday of each month" solution
last-friday-of-each-month.cob."""

import datetime

from cobol_equiv.runtime import COMP, Group, Num, Stdin, Storage, add, compute, display_line, move, subtract

DAY0 = datetime.date(1601, 1, 1).toordinal() - 1  # FUNCTION INTEGER-OF-DATE: 1601-01-01 is day 1


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = Storage("WS", [
        Group("WK-DATE", [Num("YR", "9999"), Num("MO", "99", value=1), Num("DA", "99", value=1)]),
        Num("RD-DATE", "9(8)", redefines="WK-DATE"),
        Num("INT-DATE", "9(8)", usage=COMP), Num("DOW", "9(4)", usage=COMP),
        Num("FRIDAY", "9(4)", usage=COMP, value=5),
    ])
    out = bytearray(b"Enter a calendar year (1601 thru 9999): ")
    Stdin(stdin).accept(ws["YR"])
    if not 1601 <= ws["YR"].value <= 9999:
        out += b"Invalid year\n"
        return bytes(out), {}
    for _ in range(12):
        move(1, ws["DA"])
        add(1, ws["MO"])
        if ws["MO"].value > 12:
            move(12, ws["MO"])
            move(31, ws["DA"])
        rd = int(ws["RD-DATE"].value)
        d = datetime.date(rd // 10000, rd // 100 % 100, rd % 100)
        compute(ws["INT-DATE"], d.toordinal() - DAY0)
        if not (ws["MO"].value == 12 and ws["DA"].value == 31):
            subtract(1, ws["INT-DATE"])
        dd = datetime.date.fromordinal(int(ws["INT-DATE"].value) + DAY0)
        compute(ws["RD-DATE"], dd.year * 10000 + dd.month * 100 + dd.day)
        compute(ws["DOW"], (int(ws["INT-DATE"].value) - 1) % 7 + 1)
        compute(ws["DOW"], (int(ws["DOW"].value) - int(ws["FRIDAY"].value)) % 7)
        subtract(ws["DOW"], ws["DA"])
        out += display_line(ws["YR"], "-", ws["MO"], "-", ws["DA"])
        add(1, ws["MO"])
    return bytes(out), {}

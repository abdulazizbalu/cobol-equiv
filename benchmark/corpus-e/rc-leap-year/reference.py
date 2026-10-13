"""Reference translation of the Rosetta Code "Leap year" solution leap-year-2.cob."""

import datetime

from cobol_equiv.runtime import Num, Stdin, Storage, display_line


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = Storage("WS", [Num("INPUT-YEAR", "9999")])
    out = bytearray(b"Enter calendar year (1601 thru 9999): ")
    Stdin(stdin).accept(ws["INPUT-YEAR"])
    y = int(ws["INPUT-YEAR"].value)
    if 1601 <= y <= 9999:
        # INTEGER-OF-DAY(y * 1000 + 60), then DATE-OF-INTEGER: day 60 of the year
        d = datetime.date(y, 1, 1) + datetime.timedelta(days=59)
        out += display_line("Year ", ws["INPUT-YEAR"], " ")[:-1]  # WITH NO ADVANCING
        out += b"is a leap year\n" if (d.month, d.day) == (2, 29) else b"is NOT a leap year\n"
    else:
        out += b"Input date is not within range\n"
    return bytes(out), {}

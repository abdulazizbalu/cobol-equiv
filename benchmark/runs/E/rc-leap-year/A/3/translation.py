import calendar

from cobol_equiv.runtime import (
    Storage,
    Num,
    Stdin,
    display_bytes,
    display_line,
)


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Num("INPUT-YEAR", "9999"),
    ])
    inp = Stdin(stdin)
    out = bytearray()

    out += display_bytes("Enter calendar year (1601 thru 9999): ")
    inp.accept(ws["INPUT-YEAR"])

    year = int(ws["INPUT-YEAR"].value)
    if 1601 <= year <= 9999:
        # Day 60 of the year is Feb 29 exactly when the year is a leap year
        # (Gregorian rules, as used by INTEGER-OF-DAY / DATE-OF-INTEGER).
        cal_mo_day = 229 if calendar.isleap(year) else 301
        out += display_bytes("Year ")
        out += display_bytes(ws["INPUT-YEAR"])
        out += display_bytes(" ")
        if cal_mo_day == 229:
            out += display_line("is a leap year")
        else:
            out += display_line("is NOT a leap year")
    else:
        out += display_line("Input date is not within range")

    return bytes(out), {}

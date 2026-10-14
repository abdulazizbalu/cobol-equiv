from cobol_equiv.runtime import Storage, Num, Stdin, display_line, display_bytes


def _is_leap(y: int) -> bool:
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Num("INPUT-YEAR", "9999"),
    ])
    out = bytearray()
    inp = Stdin(stdin)

    out += b"Enter calendar year (1601 thru 9999): "
    inp.accept(ws["INPUT-YEAR"])

    year = ws["INPUT-YEAR"].value
    if year >= 1601 and year <= 9999:
        y = int(year)
        out += b"Year " + display_bytes(ws["INPUT-YEAR"]) + b" "
        if _is_leap(y):
            out += display_line("is a leap year")
        else:
            out += display_line("is NOT a leap year")
    else:
        out += display_line("Input date is not within range")

    return bytes(out), {}

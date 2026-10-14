from cobol_equiv.runtime import Storage, Num, Stdin, display_bytes


def _is_leap(y: int) -> bool:
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Num("INPUT-YEAR", "9999"),
    ])
    out = bytearray()
    out += b"Enter calendar year (1601 thru 9999): "
    inp = Stdin(stdin)
    inp.accept(ws["INPUT-YEAR"])

    try:
        year = int(ws["INPUT-YEAR"].value)
    except Exception:
        digits = "".join(
            ch if ch.isdigit() else "0" for ch in ws["INPUT-YEAR"].text
        )
        year = int(digits) if digits else 0

    if 1601 <= year <= 9999:
        out += b"Year " + display_bytes(ws["INPUT-YEAR"]) + b" "
        if _is_leap(year):
            out += b"is a leap year\n"
        else:
            out += b"is NOT a leap year\n"
    else:
        out += b"Input date is not within range\n"
    return bytes(out), {}

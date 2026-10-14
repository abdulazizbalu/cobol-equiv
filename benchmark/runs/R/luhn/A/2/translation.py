from cobol_equiv.runtime import (
    Storage, Num, Alnum, move, add, display_line, refmod,
    inspect_tallying, Phrase, multiply_giving, subtract,
    divide_remainder, compute, dec,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    rec = Storage("CARD-REC", [Alnum("CD-NUMBER", "X(16)")])
    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
        Num("WS-LEN", "99"),
        Num("WS-POS", "99"),
        Num("WS-DIGIT", "9"),
        Num("WS-DOUBLE", "99"),
        Num("WS-SUM", "9(3)"),
        Num("WS-QUOT", "9(3)"),
        Num("WS-REM", "9"),
        Num("WS-CHECK", "9"),
        Alnum("WS-ODD", "X"),
        Num("WS-VALID", "9(3)", value=0),
        Num("WS-INVALID", "9(3)", value=0),
        Num("WS-REJECTED", "9(3)", value=0),
        Alnum("WS-FIXED", "X(16)"),
    ])
    out = bytearray()
    cd = rec["CD-NUMBER"]

    def luhn_sum():
        move(0, ws["WS-SUM"])
        move("N", ws["WS-ODD"])
        pos = int(ws["WS-LEN"])
        while pos >= 2:
            move(pos, ws["WS-POS"])
            move(refmod(cd, pos - 1, 1), ws["WS-DIGIT"])
            if ws["WS-ODD"].raw == b"N":
                multiply_giving(ws["WS-DIGIT"], 2, ws["WS-DOUBLE"])
                if int(ws["WS-DOUBLE"]) > 9:
                    subtract(9, ws["WS-DOUBLE"])
                add(ws["WS-DOUBLE"], ws["WS-SUM"])
                move("Y", ws["WS-ODD"])
            else:
                add(ws["WS-DIGIT"], ws["WS-SUM"])
                move("N", ws["WS-ODD"])
            pos -= 1
        move(pos, ws["WS-POS"])
        divide_remainder(ws["WS-SUM"], 10, ws["WS-QUOT"], ws["WS-REM"])
        if int(ws["WS-REM"]) == 0:
            move(0, ws["WS-CHECK"])
        else:
            compute(ws["WS-CHECK"], dec(10) - dec(ws["WS-REM"]))

    def report_card():
        ln = int(ws["WS-LEN"])
        move(refmod(cd, ln, 1), ws["WS-DIGIT"])
        if int(ws["WS-DIGIT"]) == int(ws["WS-CHECK"]):
            add(1, ws["WS-VALID"])
            out.extend(display_line("VALID ", refmod(cd, 1, ln)))
        else:
            add(1, ws["WS-INVALID"])
            move(cd, ws["WS-FIXED"])
            move(ws["WS-CHECK"], refmod(ws["WS-FIXED"], ln, 1))
            out.extend(display_line("INVALID ", refmod(cd, 1, ln), " SUM ",
                                    ws["WS-SUM"], " EXPECTED ", ws["WS-FIXED"]))

    def check_card():
        raw = cd.raw
        idx = raw.find(b" ")
        ln = len(raw) if idx < 0 else idx
        move(ln, ws["WS-LEN"])
        if ln < 2:
            add(1, ws["WS-REJECTED"])
            out.extend(display_line("SHORT [", cd, "]"))
        else:
            part = refmod(cd, 1, ln)
            if not all(0x30 <= b <= 0x39 for b in part.raw):
                add(1, ws["WS-REJECTED"])
                out.extend(display_line("NOT NUMERIC [", part, "]"))
            else:
                luhn_sum()
                report_card()

    reader = LineSequentialReader(input_files.get("CARDS.DAT", b""), 16)
    while ws["WS-EOF"].raw != b"Y":
        r = reader.read(rec.record())
        if r is None:
            move("Y", ws["WS-EOF"])
        else:
            check_card()

    out.extend(display_line("VALID ", ws["WS-VALID"], " INVALID ", ws["WS-INVALID"],
                            " REJECTED ", ws["WS-REJECTED"]))
    return bytes(out), {}

"""Reference Python translation of benchmark/corpus-r/luhn/program.cob
(MIT licensed)."""

from cobol_equiv.runtime import (Alnum, Num, Phrase, Storage, add, compute, dec, display_line,
                                 divide_remainder, inspect_tallying, move, multiply_giving,
                                 refmod, subtract)
from cobol_equiv.runtime.files import LineSequentialReader

CARD_REC = [Alnum("CD-NUMBER", "X(16)")]


def working_storage():
    return Storage("WS", [
        Num("WS-LEN", "99"), Num("WS-POS", "99"), Num("WS-DIGIT", "9"), Num("WS-DOUBLE", "99"),
        Num("WS-SUM", "9(3)"), Num("WS-QUOT", "9(3)"), Num("WS-REM", "9"), Num("WS-CHECK", "9"),
        Alnum("WS-ODD", "X"), Num("WS-VALID", "9(3)", value=0), Num("WS-INVALID", "9(3)", value=0),
        Num("WS-REJECTED", "9(3)", value=0), Alnum("WS-FIXED", "X(16)"),
    ])


def luhn_sum(cd, ws):
    move(0, ws["WS-SUM"])
    move("N", ws["WS-ODD"])
    move(ws["WS-LEN"], ws["WS-POS"])
    while not ws["WS-POS"].value < 2:
        move(refmod(cd["CD-NUMBER"], int(ws["WS-POS"].value) - 1, 1), ws["WS-DIGIT"])
        if ws["WS-ODD"].raw == b"N":
            multiply_giving(ws["WS-DIGIT"], 2, ws["WS-DOUBLE"])
            if ws["WS-DOUBLE"].value > 9:
                subtract(9, ws["WS-DOUBLE"])
            add(ws["WS-DOUBLE"], ws["WS-SUM"])
            move("Y", ws["WS-ODD"])
        else:
            add(ws["WS-DIGIT"], ws["WS-SUM"])
            move("N", ws["WS-ODD"])
        compute(ws["WS-POS"], dec(ws["WS-POS"]) - dec(1))
    divide_remainder(ws["WS-SUM"], 10, ws["WS-QUOT"], ws["WS-REM"])
    if ws["WS-REM"].value == 0:
        move(0, ws["WS-CHECK"])
    else:
        compute(ws["WS-CHECK"], dec(10) - dec(ws["WS-REM"]))


def report_card(cd, ws, out):
    n = int(ws["WS-LEN"].value)
    move(refmod(cd["CD-NUMBER"], n, 1), ws["WS-DIGIT"])
    if ws["WS-DIGIT"].value == ws["WS-CHECK"].value:
        add(1, ws["WS-VALID"])
        out += display_line("VALID ", refmod(cd["CD-NUMBER"], 1, n))
    else:
        add(1, ws["WS-INVALID"])
        move(cd["CD-NUMBER"], ws["WS-FIXED"])
        move(ws["WS-CHECK"], refmod(ws["WS-FIXED"], n, 1))
        out += display_line("INVALID ", refmod(cd["CD-NUMBER"], 1, n), " SUM ", ws["WS-SUM"], " EXPECTED ",
                            ws["WS-FIXED"])


def check_card(cd, ws, out):
    move(0, ws["WS-LEN"])
    inspect_tallying(cd["CD-NUMBER"], [Phrase("CHARACTERS", counter=ws["WS-LEN"], before=" ")])
    n = int(ws["WS-LEN"].value)
    if n < 2:
        add(1, ws["WS-REJECTED"])
        out += display_line("SHORT [", cd["CD-NUMBER"], "]")
    elif not refmod(cd["CD-NUMBER"], 1, n).raw.isdigit():
        add(1, ws["WS-REJECTED"])
        out += display_line("NOT NUMERIC [", refmod(cd["CD-NUMBER"], 1, n), "]")
    else:
        luhn_sum(cd, ws)
        report_card(cd, ws, out)


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = working_storage()
    cd = Storage("CARD-REC", CARD_REC)
    reader = LineSequentialReader(input_files["CARDS.DAT"], cd.size)
    out = bytearray()
    while reader.read(cd.record()) is not None:
        check_card(cd, ws, out)
    out += display_line("VALID ", ws["WS-VALID"], " INVALID ", ws["WS-INVALID"], " REJECTED ",
                        ws["WS-REJECTED"])
    return bytes(out), {}

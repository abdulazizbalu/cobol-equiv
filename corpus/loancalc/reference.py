"""Reference Python translation of corpus/loancalc/program.cob (MIT licensed).

Follows the cobol-equiv IO contract: main(stdin, input_files) -> (stdout, files).
"""

from cobol_equiv.runtime import (Alnum, Edited, Filler, Group, Num, Storage, add, compute, dec,
                                 display_line, move, subtract)
from cobol_equiv.runtime.files import LineSequentialReader

LOAN_REC = [
    Alnum("LN-ID", "X(6)"),
    Num("LN-PRINCIPAL", "9(7)V99"),
    Num("LN-RATE", "99V999"),
    Num("LN-TERM", "9(3)"),
]


def working_storage():
    return Storage("WS", [
        Num("WS-MRATE", "9V9(8)"),
        Num("WS-FACTOR", "9(9)V9(10)"),
        Num("WS-PAYMENT", "9(7)V99"),
        Num("WS-BALANCE", "S9(7)V99"),
        Num("WS-INTEREST", "9(7)V99"),
        Num("WS-PRINC-PART", "S9(7)V99"),
        Num("WS-TOTAL-INT", "9(8)V99"),
        Num("WS-MONTH", "9(3)"),
        Num("WS-LOANS", "9(3)", value=0),
        Num("WS-ERRORS", "9(3)", value=0),
        Group("OUT-LINE", [
            Alnum("OL-ID", "X(6)"), Filler("X", " "),
            Edited("OL-PAYMENT", "$$,$$$,$$9.99"), Filler("X", " "),
            Edited("OL-TOTAL-INT", "ZZ,ZZZ,ZZ9.99"), Filler("X", " "),
            Edited("OL-MONTHS", "ZZ9"), Filler("X", " "),
            Edited("OL-FIRST-INT", "Z,ZZZ,ZZ9.99"), Filler("X", " "),
            Edited("OL-RESIDUAL", "-(7)9.99"),
        ]),
    ])


def process_loan(ln, ws, out):
    add(1, ws["WS-LOANS"])
    if ln["LN-TERM"].value == 0:
        out += display_line(ln["LN-ID"], " ERROR TERM ZERO")
        add(1, ws["WS-ERRORS"])
        return
    compute(ws["WS-MRATE"], dec(ln["LN-RATE"]) / 1200, rounded=True)
    if ws["WS-MRATE"].value == 0:
        compute(ws["WS-PAYMENT"], dec(ln["LN-PRINCIPAL"]) / dec(ln["LN-TERM"]), rounded=True)
    else:
        move(1, ws["WS-FACTOR"])
        for _ in range(int(ln["LN-TERM"].value)):
            if compute(ws["WS-FACTOR"], dec(ws["WS-FACTOR"]) * (1 + dec(ws["WS-MRATE"])),
                       rounded=True, on_size_error=True):
                out += display_line(ln["LN-ID"], " ERROR FACTOR OVERFLOW")
                add(1, ws["WS-ERRORS"])
                return
        f = dec(ws["WS-FACTOR"])
        if compute(ws["WS-PAYMENT"], dec(ln["LN-PRINCIPAL"]) * dec(ws["WS-MRATE"]) * f / (f - 1),
                   rounded=True, on_size_error=True):
            out += display_line(ln["LN-ID"], " ERROR PAYMENT OVERFLOW")
            add(1, ws["WS-ERRORS"])
            return
    move(ln["LN-PRINCIPAL"], ws["WS-BALANCE"])
    move(0, ws["WS-TOTAL-INT"], ws["WS-MONTH"], ws["OL-FIRST-INT"])
    while not (ws["WS-BALANCE"].value <= 0 or ws["WS-MONTH"].value >= ln["LN-TERM"].value):
        add(1, ws["WS-MONTH"])
        compute(ws["WS-INTEREST"], dec(ws["WS-BALANCE"]) * dec(ws["WS-MRATE"]), rounded=True)
        if ws["WS-MONTH"].value == 1:
            move(ws["WS-INTEREST"], ws["OL-FIRST-INT"])
        compute(ws["WS-PRINC-PART"], dec(ws["WS-PAYMENT"]) - dec(ws["WS-INTEREST"]))
        if (ws["WS-PRINC-PART"].value > ws["WS-BALANCE"].value
                or ws["WS-MONTH"].value == ln["LN-TERM"].value):
            move(ws["WS-BALANCE"], ws["WS-PRINC-PART"])
        add(ws["WS-INTEREST"], ws["WS-TOTAL-INT"])
        subtract(ws["WS-PRINC-PART"], ws["WS-BALANCE"])
    move(ln["LN-ID"], ws["OL-ID"])
    move(ws["WS-PAYMENT"], ws["OL-PAYMENT"])
    move(ws["WS-TOTAL-INT"], ws["OL-TOTAL-INT"])
    move(ws["WS-MONTH"], ws["OL-MONTHS"])
    move(ws["WS-BALANCE"], ws["OL-RESIDUAL"])
    out += display_line(ws["OUT-LINE"])


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = working_storage()
    ln = Storage("LOAN-REC", LOAN_REC)
    reader = LineSequentialReader(input_files["LOANS.DAT"], ln.size)
    out = bytearray()
    while reader.read(ln.record()) is not None:
        process_loan(ln, ws, out)
    out += display_line("LOANS ", ws["WS-LOANS"], " ERRORS ", ws["WS-ERRORS"])
    return bytes(out), {}

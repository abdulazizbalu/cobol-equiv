"""Reference Python translation of benchmark/corpus-r/interest/program.cob
(MIT licensed)."""

from cobol_equiv.runtime import Alnum, Edited, Num, Storage, compute, dec, display_line, move
from cobol_equiv.runtime.files import LineSequentialReader

LOAN_REC = [Alnum("LN-ID", "X(4)"), Num("LN-PRINCIPAL", "9(7)V99"), Num("LN-RATE", "99V999"),
            Num("LN-YEARS", "99"), Num("LN-FREQ", "9")]
PERIODS = {1: 1, 2: 2, 3: 4, 4: 12}


def working_storage():
    return Storage("WS", [
        Num("WS-PERIODS", "99"), Num("WS-COUNT", "9(4)"), Num("WS-PERIOD-RATE", "9V9(8)"),
        Num("WS-FACTOR", "9(3)V9(8)"), Num("WS-SIMPLE", "S9(9)V99"), Num("WS-COMPOUND", "S9(9)V99"),
        Num("WS-MIXED", "S9(7)V9(4)"), Num("WS-AVG", "S9(9)V99"), Alnum("WS-FLAG", "X"),
        Edited("WS-OUT-1", "-(9)9.99"), Edited("WS-OUT-2", "-(9)9.99"), Edited("WS-OUT-3", "-(7)9.9(4)"),
    ])


def calc_values(ln, ws, out):
    move("N", ws["WS-FLAG"])
    p, r, y = dec(ln["LN-PRINCIPAL"]), dec(ln["LN-RATE"]), dec(ln["LN-YEARS"])
    compute(ws["WS-SIMPLE"], p * r / dec(100) * y, rounded=True)
    compute(ws["WS-PERIOD-RATE"], r / dec(100) / dec(ws["WS-PERIODS"]))
    move(1, ws["WS-FACTOR"])
    compute(ws["WS-COUNT"], dec(ws["WS-PERIODS"]) * y)
    for _ in range(int(ws["WS-COUNT"].value)):
        if compute(ws["WS-FACTOR"], dec(ws["WS-FACTOR"]) * (dec(1) + dec(ws["WS-PERIOD-RATE"])),
                   rounded=True, on_size_error=True):
            move("Y", ws["WS-FLAG"])
    if compute(ws["WS-COMPOUND"], p * dec(ws["WS-FACTOR"]) - p, rounded=True, on_size_error=True):
        move("Y", ws["WS-FLAG"])
    compute(ws["WS-MIXED"], (p + y * dec(1000)) / (r + dec(1)) - (-y) * dec("2.5")
            - dec(ws["WS-PERIODS"]) / dec(3))
    compute(ws["WS-AVG"], (dec(ws["WS-SIMPLE"]) + dec(ws["WS-COMPOUND"])) / dec(2), rounded=True)
    move(ws["WS-SIMPLE"], ws["WS-OUT-1"])
    move(ws["WS-COMPOUND"], ws["WS-OUT-2"])
    move(ws["WS-MIXED"], ws["WS-OUT-3"])
    out += display_line(ln["LN-ID"], " S", ws["WS-OUT-1"], " C", ws["WS-OUT-2"], " M", ws["WS-OUT-3"],
                        " F", ws["WS-FACTOR"], " ", ws["WS-FLAG"])
    move(ws["WS-AVG"], ws["WS-OUT-1"])
    out += display_line(ln["LN-ID"], " AVG", ws["WS-OUT-1"])


def calc_loan(ln, ws, out):
    move(PERIODS.get(int(ln["LN-FREQ"].value), 0), ws["WS-PERIODS"])
    years = ln["LN-YEARS"].value
    if ws["WS-PERIODS"].value == 0 or years == 0 or years > 40:
        out += display_line(ln["LN-ID"], " INVALID")
    else:
        calc_values(ln, ws, out)


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = working_storage()
    ln = Storage("LOAN-REC", LOAN_REC)
    reader = LineSequentialReader(input_files["LOANS.DAT"], ln.size)
    out = bytearray()
    while reader.read(ln.record()) is not None:
        calc_loan(ln, ws, out)
    return bytes(out), {}

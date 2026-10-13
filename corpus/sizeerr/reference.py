"""Reference Python translation of corpus/sizeerr/program.cob (MIT licensed)."""

from cobol_equiv.runtime import (COMP, COMP3, Alnum, Num, Storage, add, display_line,
                                 divide_into, divide_remainder, multiply, subtract)
from cobol_equiv.runtime.files import LineSequentialReader

TXN_REC = [Alnum("TX-ACCT", "X(4)"), Alnum("TX-OP", "X"), Num("TX-AMOUNT", "S9(5)V99")]


def working_storage():
    return Storage("WS", [
        Num("WS-ACC", "S9(5)V99", usage=COMP3, value=0),
        Num("WS-RAW", "S9(5)V99", value=0),
        Num("WS-BIN", "S9(4)", usage=COMP, value=0),
        Num("WS-QUOT", "S9(3)V9", value=0),
        Num("WS-REM", "S9(5)V99", value=0),
        Num("WS-ERRORS", "9(4)", value=0),
        Num("WS-COUNT", "9(4)", value=0),
    ])


def show(t, ws, out, error):
    if error:
        add(1, ws["WS-ERRORS"])
    out += display_line(t["TX-ACCT"], " ERROR " if error else " OK    ", t["TX-OP"], " ",
                        ws["WS-ACC"], " ", ws["WS-RAW"], " ", ws["WS-BIN"])


def apply_txn(t, ws, out):
    add(1, ws["WS-COUNT"])
    op = t["TX-OP"].raw
    amt = t["TX-AMOUNT"]
    if op == b"A":
        show(t, ws, out, add(amt, ws["WS-ACC"], on_size_error=True))
        add(amt, [ws["WS-RAW"], ws["WS-BIN"]])
    elif op == b"S":
        show(t, ws, out, subtract(amt, ws["WS-ACC"], on_size_error=True))
        subtract(amt, [ws["WS-RAW"], ws["WS-BIN"]])
    elif op == b"M":
        show(t, ws, out, multiply(amt, ws["WS-ACC"], rounded=True, on_size_error=True))
        multiply(amt, [(ws["WS-RAW"], True), (ws["WS-BIN"], False)])
    elif op == b"D":
        show(t, ws, out, divide_into(amt, ws["WS-ACC"], rounded=True, on_size_error=True))
        divide_into(amt, ws["WS-RAW"], rounded=True)
    elif op == b"Q":
        if divide_remainder(ws["WS-ACC"], amt, ws["WS-QUOT"], ws["WS-REM"], on_size_error=True):
            show(t, ws, out, True)
        else:
            out += display_line(t["TX-ACCT"], " Q ", ws["WS-QUOT"], " R ", ws["WS-REM"])
    else:
        out += display_line(t["TX-ACCT"], " BAD OPERATION ", t["TX-OP"])


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = working_storage()
    t = Storage("TXN-REC", TXN_REC)
    reader = LineSequentialReader(input_files["TXN.DAT"], t.size)
    out = bytearray()
    while reader.read(t.record()) is not None:
        apply_txn(t, ws, out)
    out += display_line("COUNT ", ws["WS-COUNT"], " ERRORS ", ws["WS-ERRORS"])
    out += display_line("FINAL ", ws["WS-ACC"], " ", ws["WS-RAW"], " ", ws["WS-BIN"])
    return bytes(out), {}

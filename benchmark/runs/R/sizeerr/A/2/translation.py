from cobol_equiv.runtime import (
    Storage, Num, Alnum, COMP, COMP3,
    add, subtract, multiply, divide_into, divide_remainder,
    display_line,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()

    rec = Storage("TXN-REC", [
        Alnum("TX-ACCT", "X(4)"),
        Alnum("TX-OP", "X"),
        Num("TX-AMOUNT", "S9(5)V99"),
    ])
    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
        Num("WS-ACC", "S9(5)V99", usage=COMP3, value=0),
        Num("WS-RAW", "S9(5)V99", value=0),
        Num("WS-BIN", "S9(4)", usage=COMP, value=0),
        Num("WS-QUOT", "S9(3)V9", value=0),
        Num("WS-REM", "S9(5)V99", value=0),
        Num("WS-ERRORS", "9(4)", value=0),
        Num("WS-COUNT", "9(4)", value=0),
    ])

    acct = rec["TX-ACCT"]
    op = rec["TX-OP"]
    amt = rec["TX-AMOUNT"]
    acc = ws["WS-ACC"]
    raw = ws["WS-RAW"]
    binf = ws["WS-BIN"]
    quot = ws["WS-QUOT"]
    rem = ws["WS-REM"]
    errors = ws["WS-ERRORS"]
    count = ws["WS-COUNT"]

    def show_ok():
        out.extend(display_line(acct, " OK    ", op, " ", acc, " ", raw, " ", binf))

    def show_error():
        add(1, errors)
        out.extend(display_line(acct, " ERROR ", op, " ", acc, " ", raw, " ", binf))

    def apply_txn():
        add(1, count)
        o = op.raw
        if o == b"A":
            if add(amt, acc, on_size_error=True):
                show_error()
            else:
                show_ok()
            add(amt, [raw, binf])
        elif o == b"S":
            if subtract(amt, acc, on_size_error=True):
                show_error()
            else:
                show_ok()
            subtract(amt, [raw, binf])
        elif o == b"M":
            if multiply(amt, (acc, True), on_size_error=True):
                show_error()
            else:
                show_ok()
            multiply(amt, [(raw, True), binf])
        elif o == b"D":
            if divide_into(amt, (acc, True), on_size_error=True):
                show_error()
            else:
                show_ok()
            divide_into(amt, (raw, True))
        elif o == b"Q":
            if divide_remainder(acc, amt, quot, rem, on_size_error=True):
                show_error()
            else:
                out.extend(display_line(acct, " Q ", quot, " R ", rem))
        else:
            out.extend(display_line(acct, " BAD OPERATION ", op))

    reader = LineSequentialReader(input_files.get("TXN.DAT", b""), 12)
    rec_ref = rec.record()
    while ws["WS-EOF"].raw != b"Y":
        r = reader.read(rec_ref)
        if r is None:
            ws["WS-EOF"].set_raw(b"Y")
        else:
            apply_txn()

    out.extend(display_line("COUNT ", count, " ERRORS ", errors))
    out.extend(display_line("FINAL ", acc, " ", raw, " ", binf))
    return bytes(out), {}

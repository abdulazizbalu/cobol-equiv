from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited, Filler,
    move, add, subtract, compute, dec, display_line, SPACES,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()

    rec = Storage("LOAN-REC", [
        Alnum("LN-ID", "X(6)"),
        Num("LN-PRINCIPAL", "9(7)V99"),
        Num("LN-RATE", "99V999"),
        Num("LN-TERM", "9(3)"),
    ])

    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
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
            Alnum("OL-ID", "X(6)"),
            Filler("X", value=SPACES),
            Edited("OL-PAYMENT", "$$,$$$,$$9.99"),
            Filler("X", value=SPACES),
            Edited("OL-TOTAL-INT", "ZZ,ZZZ,ZZ9.99"),
            Filler("X", value=SPACES),
            Edited("OL-MONTHS", "ZZ9"),
            Filler("X", value=SPACES),
            Edited("OL-FIRST-INT", "Z,ZZZ,ZZ9.99"),
            Filler("X", value=SPACES),
            Edited("OL-RESIDUAL", "-(7)9.99"),
        ]),
    ])

    LN_ID = rec["LN-ID"]
    LN_PRINCIPAL = rec["LN-PRINCIPAL"]
    LN_RATE = rec["LN-RATE"]
    LN_TERM = rec["LN-TERM"]
    MRATE = ws["WS-MRATE"]
    FACTOR = ws["WS-FACTOR"]
    PAYMENT = ws["WS-PAYMENT"]
    BALANCE = ws["WS-BALANCE"]
    INTEREST = ws["WS-INTEREST"]
    PRINC = ws["WS-PRINC-PART"]
    TOTAL = ws["WS-TOTAL-INT"]
    MONTH = ws["WS-MONTH"]
    LOANS = ws["WS-LOANS"]
    ERRORS = ws["WS-ERRORS"]

    def process_loan():
        add(1, LOANS)
        if LN_TERM.value == 0:
            out.extend(display_line(LN_ID, " ERROR TERM ZERO"))
            add(1, ERRORS)
            return
        compute(MRATE, dec(LN_RATE) / 1200, rounded=True)
        if MRATE.value == 0:
            compute(PAYMENT, dec(LN_PRINCIPAL) / dec(LN_TERM), rounded=True)
        else:
            move(1, FACTOR)
            times = int(LN_TERM)
            for _ in range(times):
                if compute(FACTOR, dec(FACTOR) * (dec(1) + dec(MRATE)),
                           rounded=True, on_size_error=True):
                    out.extend(display_line(LN_ID, " ERROR FACTOR OVERFLOW"))
                    add(1, ERRORS)
                    return
            if compute(PAYMENT,
                       dec(LN_PRINCIPAL) * dec(MRATE) * dec(FACTOR) / (dec(FACTOR) - 1),
                       rounded=True, on_size_error=True):
                out.extend(display_line(LN_ID, " ERROR PAYMENT OVERFLOW"))
                add(1, ERRORS)
                return
        move(LN_PRINCIPAL, BALANCE)
        move(0, TOTAL)
        move(0, MONTH)
        move(0, ws["OL-FIRST-INT"])
        while not (BALANCE.value <= 0 or MONTH.value >= LN_TERM.value):
            add(1, MONTH)
            compute(INTEREST, dec(BALANCE) * dec(MRATE), rounded=True)
            if MONTH.value == 1:
                move(INTEREST, ws["OL-FIRST-INT"])
            compute(PRINC, dec(PAYMENT) - dec(INTEREST))
            if PRINC.value > BALANCE.value or MONTH.value == LN_TERM.value:
                move(BALANCE, PRINC)
            add(INTEREST, TOTAL)
            subtract(PRINC, BALANCE)
        move(LN_ID, ws["OL-ID"])
        move(PAYMENT, ws["OL-PAYMENT"])
        move(TOTAL, ws["OL-TOTAL-INT"])
        move(MONTH, ws["OL-MONTHS"])
        move(BALANCE, ws["OL-RESIDUAL"])
        out.extend(display_line(ws["OUT-LINE"]))

    reader = LineSequentialReader(input_files.get("LOANS.DAT", b""), 23)
    while ws["WS-EOF"].text != "Y":
        r = reader.read(rec.record())
        if r is None:
            move("Y", ws["WS-EOF"])
        else:
            process_loan()

    out.extend(display_line("LOANS ", LOANS, " ERRORS ", ERRORS))
    return bytes(out), {}

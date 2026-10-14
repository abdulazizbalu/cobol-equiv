from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited, Filler,
    move, add, subtract, compute, dec, display_line,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    rec = Storage("LOAN-FILE", [
        Group("LOAN-REC", [
            Alnum("LN-ID", "X(6)"),
            Num("LN-PRINCIPAL", "9(7)V99"),
            Num("LN-RATE", "99V999"),
            Num("LN-TERM", "9(3)"),
        ]),
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
            Filler("X", " "),
            Edited("OL-PAYMENT", "$$,$$$,$$9.99"),
            Filler("X", " "),
            Edited("OL-TOTAL-INT", "ZZ,ZZZ,ZZ9.99"),
            Filler("X", " "),
            Edited("OL-MONTHS", "ZZ9"),
            Filler("X", " "),
            Edited("OL-FIRST-INT", "Z,ZZZ,ZZ9.99"),
            Filler("X", " "),
            Edited("OL-RESIDUAL", "-(7)9.99"),
        ]),
    ])

    out = bytearray()

    ln_id = rec["LN-ID"]
    ln_princ = rec["LN-PRINCIPAL"]
    ln_rate = rec["LN-RATE"]
    ln_term = rec["LN-TERM"]
    mrate = ws["WS-MRATE"]
    factor = ws["WS-FACTOR"]
    payment = ws["WS-PAYMENT"]
    balance = ws["WS-BALANCE"]
    interest = ws["WS-INTEREST"]
    pp = ws["WS-PRINC-PART"]
    totint = ws["WS-TOTAL-INT"]
    month = ws["WS-MONTH"]
    loans = ws["WS-LOANS"]
    errors = ws["WS-ERRORS"]

    def process_loan():
        add(1, loans)
        if ln_term.value == 0:
            out.extend(display_line(ln_id, " ERROR TERM ZERO"))
            add(1, errors)
            return
        compute(mrate, dec(ln_rate) / dec(1200), rounded=True)
        if mrate.value == 0:
            compute(payment, dec(ln_princ) / dec(ln_term), rounded=True)
        else:
            move(1, factor)
            n = int(ln_term.value)
            for _ in range(n):
                err = compute(factor, dec(factor) * (dec(1) + dec(mrate)),
                              rounded=True, on_size_error=True)
                if err:
                    out.extend(display_line(ln_id, " ERROR FACTOR OVERFLOW"))
                    add(1, errors)
                    return
            err = compute(payment,
                          dec(ln_princ) * dec(mrate) * dec(factor) / (dec(factor) - dec(1)),
                          rounded=True, on_size_error=True)
            if err:
                out.extend(display_line(ln_id, " ERROR PAYMENT OVERFLOW"))
                add(1, errors)
                return
        move(ln_princ, balance)
        move(0, totint, month, ws["OL-FIRST-INT"])
        while not (balance.value <= 0 or month.value >= ln_term.value):
            add(1, month)
            compute(interest, dec(balance) * dec(mrate), rounded=True)
            if month.value == 1:
                move(interest, ws["OL-FIRST-INT"])
            compute(pp, dec(payment) - dec(interest))
            if pp.value > balance.value or month.value == ln_term.value:
                move(balance, pp)
            add(interest, totint)
            subtract(pp, balance)
        move(ln_id, ws["OL-ID"])
        move(payment, ws["OL-PAYMENT"])
        move(totint, ws["OL-TOTAL-INT"])
        move(month, ws["OL-MONTHS"])
        move(balance, ws["OL-RESIDUAL"])
        out.extend(display_line(ws["OUT-LINE"]))

    reader = LineSequentialReader(input_files.get("LOANS.DAT", b""), 23)
    while ws["WS-EOF"].text != "Y":
        r = reader.read(rec.record())
        if r is None:
            move("Y", ws["WS-EOF"])
        else:
            process_loan()

    out.extend(display_line("LOANS ", loans, " ERRORS ", errors))
    return bytes(out), {}

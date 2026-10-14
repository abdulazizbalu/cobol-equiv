from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited, move, compute, dec, display_line,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    rec = Storage("LOAN-FILE", [
        Group("LOAN-REC", [
            Alnum("LN-ID", "X(4)"),
            Num("LN-PRINCIPAL", "9(7)V99"),
            Num("LN-RATE", "99V999"),
            Num("LN-YEARS", "99"),
            Num("LN-FREQ", "9"),
        ]),
    ])
    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
        Num("WS-PERIODS", "99"),
        Num("WS-COUNT", "9(4)"),
        Num("WS-PERIOD-RATE", "9V9(8)"),
        Num("WS-FACTOR", "9(3)V9(8)"),
        Num("WS-SIMPLE", "S9(9)V99"),
        Num("WS-COMPOUND", "S9(9)V99"),
        Num("WS-MIXED", "S9(7)V9(4)"),
        Num("WS-AVG", "S9(9)V99"),
        Alnum("WS-FLAG", "X"),
        Edited("WS-OUT-1", "-(9)9.99"),
        Edited("WS-OUT-2", "-(9)9.99"),
        Edited("WS-OUT-3", "-(7)9.9(4)"),
    ])

    out = bytearray()
    ln_id = rec["LN-ID"]
    principal = rec["LN-PRINCIPAL"]
    rate = rec["LN-RATE"]
    years = rec["LN-YEARS"]
    freq = rec["LN-FREQ"]
    periods = ws["WS-PERIODS"]
    count = ws["WS-COUNT"]
    prate = ws["WS-PERIOD-RATE"]
    factor = ws["WS-FACTOR"]
    simple = ws["WS-SIMPLE"]
    compound = ws["WS-COMPOUND"]
    mixed = ws["WS-MIXED"]
    avg = ws["WS-AVG"]
    flag = ws["WS-FLAG"]
    out1 = ws["WS-OUT-1"]
    out2 = ws["WS-OUT-2"]
    out3 = ws["WS-OUT-3"]

    def calc_values():
        move("N", flag)
        compute(simple, dec(principal) * dec(rate) / 100 * dec(years), rounded=True)
        compute(prate, dec(rate) / 100 / dec(periods))
        move(1, factor)
        compute(count, dec(periods) * dec(years))
        n = int(count)
        for _ in range(n):
            if compute(factor, dec(factor) * (dec(1) + dec(prate)),
                       rounded=True, on_size_error=True):
                move("Y", flag)
        if compute(compound, dec(principal) * dec(factor) - dec(principal),
                   rounded=True, on_size_error=True):
            move("Y", flag)
        compute(mixed,
                (dec(principal) + dec(years) * 1000) / (dec(rate) + 1)
                - (-dec(years)) * dec("2.5") - dec(periods) / 3)
        compute(avg, (dec(simple) + dec(compound)) / 2, rounded=True)
        move(simple, out1)
        move(compound, out2)
        move(mixed, out3)
        out.extend(display_line(ln_id, " S", out1, " C", out2, " M", out3,
                                " F", factor, " ", flag))
        move(avg, out1)
        out.extend(display_line(ln_id, " AVG", out1))

    def calc_loan():
        f = int(freq)
        if f == 1:
            move(1, periods)
        elif f == 2:
            move(2, periods)
        elif f == 3:
            move(4, periods)
        elif f == 4:
            move(12, periods)
        else:
            move(0, periods)
        y = int(years)
        if int(periods) == 0 or y == 0 or y > 40:
            out.extend(display_line(ln_id, " INVALID"))
        else:
            calc_values()

    reader = LineSequentialReader(input_files.get("LOANS.DAT", b""), 21)
    while ws["WS-EOF"].text != "Y":
        r = reader.read(rec.record())
        if r is None:
            move("Y", ws["WS-EOF"])
        else:
            calc_loan()

    return bytes(out), {}

import datetime

from cobol_equiv.runtime import (
    Storage, Group, Num, COMP, move, add, subtract,
    display_line, display_bytes, Stdin,
)

_BASE = datetime.date(1601, 1, 1).toordinal()


def _integer_of_date(n: int) -> int:
    y, rest = divmod(n, 10000)
    m, d = divmod(rest, 100)
    return datetime.date(y, m, d).toordinal() - _BASE + 1


def _date_of_integer(i: int) -> int:
    d = datetime.date.fromordinal(i + _BASE - 1)
    return d.year * 10000 + d.month * 100 + d.day


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Group("WK-DATE", [
            Num("YR", "9999"),
            Num("MO", "99", value=1),
            Num("DA", "99", value=1),
        ]),
        Num("RD-DATE", "9(8)", redefines="WK-DATE"),
        Group("BIN", [
            Num("INT-DATE", "9(8)", usage=COMP),
            Num("DOW", "9(4)", usage=COMP),
            Num("FRIDAY", "9(4)", usage=COMP, value=5),
        ]),
    ])
    out = bytearray()
    inp = Stdin(stdin)

    out += display_bytes("Enter a calendar year (1601 thru 9999): ")
    inp.accept(ws["YR"])
    yr = int(ws["YR"])
    if not (1601 <= yr <= 9999):
        out += display_line("Invalid year")
        return bytes(out), {}

    yr_f, mo, da = ws["YR"], ws["MO"], ws["DA"]
    rd, int_date, dow, friday = ws["RD-DATE"], ws["INT-DATE"], ws["DOW"], ws["FRIDAY"]

    for _ in range(12):
        move(1, da)
        add(1, mo)
        if int(mo) > 12:
            move(12, mo)
            move(31, da)
        move(_integer_of_date(int(rd)), int_date)
        if int(mo) == 12 and int(da) == 31:
            pass
        else:
            subtract(1, int_date)
        move(_date_of_integer(int(int_date)), rd)
        move((int(int_date) - 1) % 7 + 1, dow)
        move((int(dow) - int(friday)) % 7, dow)
        subtract(dow, da)
        out += display_line(yr_f, "-", mo, "-", da)
        add(1, mo)

    return bytes(out), {}

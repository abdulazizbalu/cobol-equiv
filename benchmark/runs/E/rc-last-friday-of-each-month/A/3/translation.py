from datetime import date

from cobol_equiv.runtime import Storage, Group, Num, Stdin

_BASE = date(1600, 12, 31).toordinal()


def _integer_of_date(y, m, d):
    return date(y, m, d).toordinal() - _BASE


def _date_of_integer(n):
    dt = date.fromordinal(n + _BASE)
    return dt.year, dt.month, dt.day


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()
    ws = Storage("WS", [
        Group("WK-DATE", [
            Num("YR", "9999"),
            Num("MO", "99", value=1),
            Num("DA", "99", value=1),
        ]),
    ])
    inp = Stdin(stdin)
    out += b"Enter a calendar year (1601 thru 9999): "
    inp.accept(ws["YR"])
    yr = int(ws["YR"])
    if not (1601 <= yr <= 9999):
        out += b"Invalid year\n"
        return bytes(out), {}
    mo = 1
    da = 1
    friday = 5
    for _ in range(12):
        da = 1
        mo += 1
        if mo > 12:
            mo = 12
            da = 31
        int_date = _integer_of_date(yr, mo, da)
        if not (mo == 12 and da == 31):
            int_date -= 1
        yr, mo, da = _date_of_integer(int_date)
        dow = (int_date - 1) % 7 + 1
        dow = (dow - friday) % 7
        da -= dow
        out += f"{yr:04d}-{mo:02d}-{da:02d}\n".encode("latin-1")
        mo += 1
    return bytes(out), {}

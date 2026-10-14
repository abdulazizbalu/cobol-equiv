import datetime

from cobol_equiv.runtime import Storage, Group, Num, Stdin


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Group("WK-DATE", [
            Num("YR", "9999"),
            Num("MO", "99", value=1),
            Num("DA", "99", value=1),
        ]),
    ])
    out = bytearray()
    out += b"Enter a calendar year (1601 thru 9999): "
    inp = Stdin(stdin)
    inp.accept(ws["YR"])
    try:
        yr = int(ws["YR"])
    except Exception:
        yr = 0
    if not (1601 <= yr <= 9999):
        out += b"Invalid year\n"
        return bytes(out), {}

    for mo in range(1, 13):
        if mo == 12:
            d = datetime.date(yr, 12, 31)
        else:
            d = datetime.date(yr, mo + 1, 1) - datetime.timedelta(days=1)
        back = (d.weekday() - 4) % 7
        da = d.day - back
        out += ("%04d-%02d-%02d\n" % (yr, d.month, da)).encode("latin-1")
    return bytes(out), {}

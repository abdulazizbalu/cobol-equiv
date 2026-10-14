from cobol_equiv.runtime import Storage, Num, Alnum, add, display_bytes
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    rec = Storage("CARD-REC", [Alnum("CD-NUMBER", "X(16)")])
    ws = Storage("WS", [
        Num("WS-VALID", "9(3)", value=0),
        Num("WS-INVALID", "9(3)", value=0),
        Num("WS-REJECTED", "9(3)", value=0),
    ])
    out = bytearray()
    reader = LineSequentialReader(input_files.get("CARDS.DAT", b""), 16)

    while True:
        r = reader.read(rec.record())
        if r is None:
            break
        cd = bytes(rec["CD-NUMBER"].raw)
        # INSPECT TALLYING CHARACTERS BEFORE INITIAL SPACE
        idx = cd.find(b" ")
        ln = len(cd) if idx < 0 else idx
        if ln < 2:
            add(1, ws["WS-REJECTED"])
            out += b"SHORT [" + cd + b"]\n"
            continue
        part = cd[:ln]
        if not all(0x30 <= c <= 0x39 for c in part):
            add(1, ws["WS-REJECTED"])
            out += b"NOT NUMERIC [" + part + b"]\n"
            continue
        # LUHN-SUM
        total = 0
        odd = False
        pos = ln
        while not (pos < 2):
            d = cd[pos - 2] - 0x30
            if not odd:
                dbl = d * 2
                if dbl > 9:
                    dbl -= 9
                total += dbl
                odd = True
            else:
                total += d
                odd = False
            pos -= 1
        total %= 1000
        rem = total % 10
        check = 0 if rem == 0 else 10 - rem
        # REPORT-CARD
        last = cd[ln - 1] - 0x30
        if last == check:
            add(1, ws["WS-VALID"])
            out += b"VALID " + part + b"\n"
        else:
            add(1, ws["WS-INVALID"])
            fixed = bytearray(cd)
            fixed[ln - 1] = 0x30 + check
            out += (b"INVALID " + part + b" SUM " + b"%03d" % total
                    + b" EXPECTED " + bytes(fixed) + b"\n")

    out += (b"VALID " + display_bytes(ws["WS-VALID"])
            + b" INVALID " + display_bytes(ws["WS-INVALID"])
            + b" REJECTED " + display_bytes(ws["WS-REJECTED"]) + b"\n")
    return bytes(out), {}

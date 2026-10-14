from cobol_equiv.runtime import Storage, Group, Alnum
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    rec = Storage("CARD-REC", [
        Group("CARD-REC", [Alnum("CD-NUMBER", "X(16)")]),
    ])
    cd = rec["CD-NUMBER"]
    reader = LineSequentialReader(input_files.get("CARDS.DAT", b""), 16)

    out = bytearray()
    valid = 0
    invalid = 0
    rejected = 0

    while True:
        r = reader.read(rec.record())
        if r is None:
            break
        num = cd.raw
        # INSPECT TALLYING CHARACTERS BEFORE INITIAL SPACE
        idx = num.find(b" ")
        ln = 16 if idx < 0 else idx
        if ln < 2:
            rejected = (rejected + 1) % 1000
            out += b"SHORT [" + num + b"]\n"
            continue
        part = num[:ln]
        if not all(0x30 <= c <= 0x39 for c in part):
            rejected = (rejected + 1) % 1000
            out += b"NOT NUMERIC [" + part + b"]\n"
            continue
        # LUHN-SUM
        s = 0
        odd = False
        pos = ln
        while not pos < 2:
            d = part[pos - 2] - 0x30
            if not odd:
                dbl = d * 2
                if dbl > 9:
                    dbl -= 9
                s += dbl
                odd = True
            else:
                s += d
                odd = False
            pos -= 1
        s %= 1000
        rem = s % 10
        check = 0 if rem == 0 else 10 - rem
        # REPORT-CARD
        last = part[ln - 1] - 0x30
        if last == check:
            valid = (valid + 1) % 1000
            out += b"VALID " + part + b"\n"
        else:
            invalid = (invalid + 1) % 1000
            fixed = bytearray(num)
            fixed[ln - 1] = 0x30 + check
            out += (b"INVALID " + part + b" SUM " + f"{s:03d}".encode()
                    + b" EXPECTED " + bytes(fixed) + b"\n")

    out += (f"VALID {valid:03d} INVALID {invalid:03d} REJECTED {rejected:03d}\n").encode()
    return bytes(out), {}

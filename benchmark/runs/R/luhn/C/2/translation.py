def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get("CARDS.DAT", b"")
    out = []
    valid = 0
    invalid = 0
    rejected = 0

    # Split into LINE SEQUENTIAL records
    records = []
    if data:
        parts = data.split(b"\n")
        if data.endswith(b"\n"):
            parts = parts[:-1]
        records = parts

    for raw in records:
        rec = raw[:16]
        if len(rec) < 16:
            rec = rec + b" " * (16 - len(rec))

        # INSPECT ... FOR CHARACTERS BEFORE INITIAL SPACE
        idx = rec.find(b" ")
        ln = 16 if idx < 0 else idx

        if ln < 2:
            rejected = (rejected + 1) % 1000
            out.append(b"SHORT [" + rec + b"]\n")
            continue

        part = rec[:ln]
        if not all(0x30 <= c <= 0x39 for c in part):
            rejected = (rejected + 1) % 1000
            out.append(b"NOT NUMERIC [" + part + b"]\n")
            continue

        # LUHN-SUM
        s = 0
        odd = False
        pos = ln
        while pos >= 2:
            d = rec[pos - 2] - 0x30
            if not odd:
                dbl = d * 2
                if dbl > 9:
                    dbl -= 9
                s = (s + dbl) % 1000
                odd = True
            else:
                s = (s + d) % 1000
                odd = False
            pos -= 1
        rem = s % 10
        check = 0 if rem == 0 else 10 - rem

        # REPORT-CARD
        digit = rec[ln - 1] - 0x30
        if digit == check:
            valid = (valid + 1) % 1000
            out.append(b"VALID " + part + b"\n")
        else:
            invalid = (invalid + 1) % 1000
            fixed = bytearray(rec)
            fixed[ln - 1] = 0x30 + check
            out.append(b"INVALID " + part + b" SUM " + b"%03d" % s +
                       b" EXPECTED " + bytes(fixed) + b"\n")

    out.append(b"VALID %03d INVALID %03d REJECTED %03d\n" % (valid, invalid, rejected))
    return b"".join(out), {}

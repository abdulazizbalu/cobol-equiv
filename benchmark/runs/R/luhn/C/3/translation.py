def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get('CARDS.DAT', b'')
    lines = data.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()

    out = []
    valid = invalid = rejected = 0

    for raw in lines:
        rec = raw[:16].ljust(16, b' ')

        idx = rec.find(b' ')
        length = 16 if idx < 0 else idx

        if length < 2:
            rejected = (rejected + 1) % 1000
            out.append(b'SHORT [' + rec + b']\n')
            continue

        part = rec[:length]
        if not all(48 <= c <= 57 for c in part):
            rejected = (rejected + 1) % 1000
            out.append(b'NOT NUMERIC [' + part + b']\n')
            continue

        # LUHN-SUM
        total = 0
        odd = False
        pos = length
        while not (pos < 2):
            d = rec[pos - 2] - 48
            if not odd:
                dbl = d * 2
                if dbl > 9:
                    dbl -= 9
                total = (total + dbl) % 1000
                odd = True
            else:
                total = (total + d) % 1000
                odd = False
            pos -= 1
        rem = total % 10
        check = 0 if rem == 0 else 10 - rem

        # REPORT-CARD
        last = rec[length - 1] - 48
        if last == check:
            valid = (valid + 1) % 1000
            out.append(b'VALID ' + part + b'\n')
        else:
            invalid = (invalid + 1) % 1000
            fixed = bytearray(rec)
            fixed[length - 1] = 48 + check
            out.append(b'INVALID ' + part + b' SUM ' + b'%03d' % total +
                       b' EXPECTED ' + bytes(fixed) + b'\n')

    out.append(b'VALID %03d INVALID %03d REJECTED %03d\n' % (valid, invalid, rejected))
    return b''.join(out), {}

def _unpack_comp3(b):
    digits = []
    for i, byte in enumerate(b):
        hi = (byte >> 4) & 0x0F
        lo = byte & 0x0F
        digits.append(hi % 10)
        if i < len(b) - 1:
            digits.append(lo % 10)
    value = 0
    for d in digits:
        value = value * 10 + d
    return value  # sign ignored for unsigned edited output


def _edit_currency(value_cents):
    # PIC $$,$$$,$$9.99 (13 chars), unsigned, 7 integer digits
    value_cents = abs(value_cents) % 1000000000
    intpart = value_cents // 100
    frac = value_cents % 100
    s = "${:,}.{:02d}".format(intpart, frac)
    return s.rjust(13).encode("ascii")


def main(stdin, input_files):
    data = input_files.get("ACCTREC", b"")
    reclen = 170
    out = bytearray()
    nrec = len(data) // reclen
    for r in range(nrec):
        rec = data[r * reclen:(r + 1) * reclen]
        acct_no = rec[0:8]
        limit = _unpack_comp3(rec[8:13])
        balance = _unpack_comp3(rec[13:18])
        last_name = rec[18:38]
        first_name = rec[38:53]
        comments = rec[120:170]
        line = (acct_no + _edit_currency(limit) + _edit_currency(balance)
                + last_name + first_name + comments)
        out += line
    return b"", {"PRTLINE": bytes(out)}

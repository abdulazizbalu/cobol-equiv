def _unpack_comp3(b):
    digits = []
    for i, byte in enumerate(b):
        hi = byte >> 4
        lo = byte & 0x0F
        digits.append(hi)
        if i < len(b) - 1:
            digits.append(lo)
    val = 0
    for d in digits:
        val = val * 10 + (d % 10 if d > 9 else d)
    return val  # sign ignored: edited field has no sign position


def _edit_money(val):
    # val is integer in hundredths, unsigned; PIC $$,$$$,$$9.99
    val = val % 10 ** 9
    ip = val // 100
    dp = val % 100
    s = "$" + format(ip, ",")
    return s.rjust(10) + "." + "%02d" % dp


def main(stdin, input_files):
    data = input_files.get("ACCTREC", b"")
    reclen = 170
    out = bytearray()
    pos = 0
    n = len(data)
    while pos < n:
        rec = data[pos:pos + reclen]
        pos += reclen
        if len(rec) < reclen:
            rec = rec + b" " * (reclen - len(rec))
        acct_no = rec[0:8]
        limit = _unpack_comp3(rec[8:13])
        balance = _unpack_comp3(rec[13:18])
        last = rec[18:38]
        first = rec[38:53]
        comments = rec[120:170]
        line = (acct_no
                + _edit_money(limit).encode("latin-1")
                + _edit_money(balance).encode("latin-1")
                + last + first + comments)
        out += line
    return b"", {"PRTLINE": bytes(out)}

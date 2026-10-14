def _d2i(c):
    return c & 0x0F


def _decode_last(c):
    """Return (digit, negative) for trailing embedded sign byte."""
    if 0x30 <= c <= 0x39:
        return c - 0x30, False
    if 0x70 <= c <= 0x79:
        return c - 0x70, True
    if c == 0x7B:  # '{'
        return 0, False
    if c == 0x7D:  # '}'
        return 0, True
    if 0x41 <= c <= 0x49:  # 'A'..'I'
        return c - 0x40, False
    if 0x4A <= c <= 0x52:  # 'J'..'R'
        return c - 0x49, True
    return _d2i(c), False


def _numval(b, signed=False):
    if not signed:
        v = 0
        for c in b:
            v = v * 10 + _d2i(c)
        return v
    v = 0
    for c in b[:-1]:
        v = v * 10 + _d2i(c)
    d, neg = _decode_last(b[-1])
    v = v * 10 + d
    return -v if neg else v


def _display_signed_raw(b, int_digits):
    # b: raw bytes of S9(n)V99 field
    last = b[-1]
    d, neg = _decode_last(last)
    if 0x30 <= last <= 0x39 or 0x70 <= last <= 0x79 or last in (0x7B, 0x7D) \
            or 0x41 <= last <= 0x52:
        lastch = bytes([0x30 + d])
    else:
        lastch = bytes([last])
    digits = bytes(b[:-1]) + lastch
    return (b'-' if neg else b'+') + digits[:int_digits] + b'.' + digits[int_digits:]


def _fmt_signed(cents, int_digits):
    neg = cents < 0
    a = abs(cents)
    s = str(a).rjust(int_digits + 2, '0')
    return (('-' if neg else '+') + s[:int_digits] + '.' + s[int_digits:]).encode('latin-1')


def _edit(cents):
    neg = cents < 0
    a = abs(cents)
    ip = (a // 100) % 100000000
    cp = a % 100
    s = ('-' if neg else '') + format(ip, ',') + '.' + str(cp).rjust(2, '0')
    return s.rjust(14).encode('latin-1')


def _trunc(v, mod):
    if v < 0:
        return -((-v) % mod)
    return v % mod


def main(stdin, input_files):
    out = []
    data = input_files.get('RECS.DAT', b'')
    lines = data.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
    days = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    run_count = 0
    run_total = 0  # cents
    for line in lines:
        rec = line[:30].ljust(30, b' ')
        t = rec[0:1]
        body = rec[1:30]
        if t == b'H':
            name = body[0:20]
            date = body[20:28]
            yyyy = date[0:4]
            mm = date[4:6]
            dd = date[6:8]
            ok = b'Y'
            m = _numval(mm)
            if m < 1 or m > 12:
                ok = b'N'
            else:
                dv = _numval(dd)
                if dv < 1 or dv > days[m - 1]:
                    ok = b'N'
            out.append(b'HEADER ' + name + b' ' + yyyy + b'-' + mm + b'-' + dd
                       + b' ' + ok + b' ' + date + b'\n')
        elif t == b'D':
            item = body[0:5]
            qty = _numval(body[5:9], True)
            price = _numval(body[9:16])
            disc = _numval(body[16:18])
            x = qty * price * (100 - disc)
            q = abs(x)
            c = (q + 50) // 100
            amt = -c if x < 0 else c
            amt = _trunc(amt, 10 ** 11)
            ed = _edit(amt)
            run_count = (run_count + 1) % 100000
            run_total = _trunc(run_total + amt, 10 ** 11)
            out.append(b'DETAIL ' + item + b' ' + ed + b'\n')
        elif t == b'T':
            cnt_raw = body[0:5]
            tot_raw = body[5:16]
            cnt = _numval(cnt_raw)
            tot = _numval(tot_raw, True)
            if cnt == run_count and tot == run_total:
                out.append(b'TRAILER OK ' + cnt_raw + b'\n')
            else:
                out.append(b'TRAILER MISMATCH ' + cnt_raw + b' '
                           + _display_signed_raw(tot_raw, 9) + b' '
                           + str(run_count).rjust(5, '0').encode() + b' '
                           + _fmt_signed(run_total, 9) + b'\n')
            run_count = 0
            run_total = 0
        else:
            out.append(b'UNKNOWN TYPE ' + t + b'\n')
    out.append(b'OPEN COUNT ' + str(run_count).rjust(5, '0').encode()
               + b' TOTAL ' + _fmt_signed(run_total, 9) + b'\n')
    return b''.join(out), {}

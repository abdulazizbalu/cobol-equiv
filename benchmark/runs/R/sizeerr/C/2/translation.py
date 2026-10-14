from fractions import Fraction


def _decode_amount(field):
    # field: 7 bytes, PIC S9(5)V99 DISPLAY with trailing overpunch sign (ASCII)
    last = field[-1]
    sign = 1
    if 0x30 <= last <= 0x39:
        ld = last - 0x30
    elif 0x70 <= last <= 0x79:
        ld = last - 0x70
        sign = -1
    else:
        ld = 0
    digits = [b & 0x0F for b in field[:-1]] + [ld]
    n = 0
    for d in digits:
        n = n * 10 + d
    return Fraction(sign * n, 100)


def _store(val, scale, digits, rounded, keep, binary=False):
    """Returns None on overflow with keep, else (int_value, negzero_flag)."""
    x = val * (10 ** scale)
    neg = x < 0
    a = -x if neg else x
    if rounded:
        q = (2 * a.numerator + a.denominator) // (2 * a.denominator)
    else:
        q = a.numerator // a.denominator
    sgn = 0 if q == 0 else (-1 if neg else 1)
    lim = 10 ** digits
    if q >= lim:
        if keep:
            return None
        q %= lim
    v = -q if sgn < 0 else q
    negzero = (not binary) and sgn < 0 and q == 0
    return (v, negzero)


def _fmt(v, digits, scale, negflag=False):
    s = b'-' if (v < 0 or negflag) else b'+'
    a = str(abs(v)).zfill(digits)
    if scale:
        a = a[:-scale] + '.' + a[-scale:]
    return s + a.encode('ascii')


def main(stdin, input_files):
    data = input_files.get('TXN.DAT', b'')
    lines = data.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
    out = []

    acc = 0
    raw = 0
    raw_neg = False
    bin_ = 0
    quot = 0
    rem = 0
    errors = 0
    count = 0

    for line in lines:
        rec = line[:12]
        rec = rec + b' ' * (12 - len(rec))
        acct = rec[0:4]
        op = rec[4:5]
        amt = _decode_amount(rec[5:12])
        count = (count + 1) % 10000

        def show(kind):
            out.append(acct + kind + op + b' ' + _fmt(acc, 7, 2) + b' ' +
                       _fmt(raw, 7, 2, raw_neg) + b' ' + _fmt(bin_, 4, 0) + b'\n')

        def show_ok():
            show(b' OK    ')

        def show_err():
            nonlocal errors
            errors = (errors + 1) % 10000
            show(b' ERROR ')

        if op == b'A' or op == b'S':
            sgn = 1 if op == b'A' else -1
            r = _store(Fraction(acc, 100) + sgn * amt, 2, 7, False, True)
            if r is None:
                show_err()
            else:
                acc = r[0]
                show_ok()
            r = _store(Fraction(raw, 100) + sgn * amt, 2, 7, False, False)
            raw, raw_neg = r
            r = _store(Fraction(bin_) + sgn * amt, 0, 4, False, False, True)
            bin_ = r[0]
        elif op == b'M':
            r = _store(Fraction(acc, 100) * amt, 2, 7, True, True)
            if r is None:
                show_err()
            else:
                acc = r[0]
                show_ok()
            r = _store(Fraction(raw, 100) * amt, 2, 7, True, False)
            raw, raw_neg = r
            r = _store(Fraction(bin_) * amt, 0, 4, False, False, True)
            bin_ = r[0]
        elif op == b'D':
            if amt == 0:
                show_err()
            else:
                r = _store(Fraction(acc, 100) / amt, 2, 7, True, True)
                if r is None:
                    show_err()
                else:
                    acc = r[0]
                    show_ok()
            if amt != 0:
                r = _store(Fraction(raw, 100) / amt, 2, 7, True, False)
                raw, raw_neg = r
        elif op == b'Q':
            if amt == 0:
                show_err()
            else:
                dividend = Fraction(acc, 100)
                q = dividend / amt
                rq = _store(q, 1, 4, False, True)
                x = q * 10
                qi = abs(x.numerator) // x.denominator
                if x < 0:
                    qi = -qi
                qt = Fraction(qi, 10)
                remv = dividend - qt * amt
                rr = _store(remv, 2, 7, False, True)
                if rr is not None:
                    rem = rr[0]
                if rq is None:
                    show_err()
                else:
                    quot = rq[0]
                    out.append(acct + b' Q ' + _fmt(quot, 4, 1) + b' R ' +
                               _fmt(rem, 7, 2) + b'\n')
        else:
            out.append(acct + b' BAD OPERATION ' + op + b'\n')

    out.append(b'COUNT ' + str(count).zfill(4).encode() + b' ERRORS ' +
               str(errors).zfill(4).encode() + b'\n')
    out.append(b'FINAL ' + _fmt(acc, 7, 2) + b' ' + _fmt(raw, 7, 2, raw_neg) +
               b' ' + _fmt(bin_, 4, 0) + b'\n')
    return b''.join(out), {}

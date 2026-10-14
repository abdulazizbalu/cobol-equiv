from fractions import Fraction


def _parse_zoned(b):
    """Parse a PIC S9(5)V99 DISPLAY field (trailing embedded sign) as an
    integer scaled by 100."""
    val = 0
    n = len(b)
    neg = False
    for i, c in enumerate(b):
        if i == n - 1:
            if 0x30 <= c <= 0x39:
                d = c - 0x30
            elif c == 0x20:
                d = 0
            elif 0x70 <= c <= 0x79:  # 'p'..'y' negative overpunch
                d = c - 0x70
                neg = True
            elif c == 0x7D:  # '}'
                d = 0
                neg = True
            elif 0x4A <= c <= 0x52:  # 'J'..'R'
                d = c - 0x49
                neg = True
            elif c == 0x7B:  # '{'
                d = 0
            elif 0x41 <= c <= 0x49:  # 'A'..'I'
                d = c - 0x40
            else:
                d = c & 0x0F
                if d > 9:
                    d = d % 10
        else:
            d = c & 0x0F
            if d > 9:
                d = d % 10
        val = val * 10 + d
    return -val if neg else val


def _trunc_div(a, b):
    # integer division truncating toward zero
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def _scale_value(v, scale, rounded):
    """v: Fraction. Return integer v*10^scale, truncated or rounded half away."""
    x = v * (10 ** scale)
    num, den = x.numerator, x.denominator
    if rounded:
        a = abs(num)
        q, r = divmod(a, den)
        if 2 * r >= den:
            q += 1
        return q if num >= 0 else -q
    return _trunc_div(num, den)


def _store(v, scale, digits, rounded, keep):
    """Return new scaled integer or None when size error with KEEP."""
    s = _scale_value(v, scale, rounded)
    lim = 10 ** digits
    if abs(s) >= lim:
        if keep:
            return None
        r = abs(s) % lim
        s = r if s >= 0 else -r
    return s


def _fmt_signed(val, intdigits, scale):
    sign = "+" if val >= 0 else "-"
    a = abs(val)
    s = str(a).rjust(intdigits + scale, "0")
    if scale > 0:
        return sign + s[:intdigits] + "." + s[intdigits:]
    return sign + s


def _fmt_unsigned(val, digits):
    return str(abs(val) % (10 ** digits)).rjust(digits, "0")


def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get("TXN.DAT", b"")
    out = []

    # Split into line-sequential records
    records = []
    if data:
        parts = data.split(b"\n")
        if parts and parts[-1] == b"":
            parts = parts[:-1]
        for p in parts:
            rec = p[:12]
            if len(rec) < 12:
                rec = rec + b" " * (12 - len(rec))
            records.append(rec)

    acc = 0     # scaled by 100, S9(5)V99
    raw = 0     # scaled by 100, S9(5)V99
    binv = 0    # S9(4)
    quot = 0    # scaled by 10, S9(3)V9
    rem = 0     # scaled by 100, S9(5)V99
    errors = 0
    count = 0

    def F(x, sc):
        return Fraction(x, 10 ** sc)

    for rec in records:
        acct = rec[0:4]
        op = rec[4:5]
        amt_i = _parse_zoned(rec[5:12])
        amt = F(amt_i, 2)
        count = (count + 1) % 10000

        def line(kind):
            return (acct + kind + op + b" " +
                    _fmt_signed(acc, 5, 2).encode() + b" " +
                    _fmt_signed(raw, 5, 2).encode() + b" " +
                    _fmt_signed(binv, 4, 0).encode())

        def show_ok():
            out.append(line(b" OK    "))

        def show_error():
            nonlocal errors
            errors = (errors + 1) % 10000
            out.append(line(b" ERROR "))

        if op == b"A":
            r = _store(F(acc, 2) + amt, 2, 7, False, True)
            if r is None:
                show_error()
            else:
                acc = r
                show_ok()
            raw = _store(F(raw, 2) + amt, 2, 7, False, False)
            binv = _store(Fraction(binv) + amt, 0, 4, False, False)
        elif op == b"S":
            r = _store(F(acc, 2) - amt, 2, 7, False, True)
            if r is None:
                show_error()
            else:
                acc = r
                show_ok()
            raw = _store(F(raw, 2) - amt, 2, 7, False, False)
            binv = _store(Fraction(binv) - amt, 0, 4, False, False)
        elif op == b"M":
            r = _store(F(acc, 2) * amt, 2, 7, True, True)
            if r is None:
                show_error()
            else:
                acc = r
                show_ok()
            raw = _store(F(raw, 2) * amt, 2, 7, True, False)
            binv = _store(Fraction(binv) * amt, 0, 4, False, False)
        elif op == b"D":
            if amt_i == 0:
                show_error()
            else:
                r = _store(F(acc, 2) / amt, 2, 7, True, True)
                if r is None:
                    show_error()
                else:
                    acc = r
                    show_ok()
            if amt_i != 0:
                raw = _store(F(raw, 2) / amt, 2, 7, True, False)
        elif op == b"Q":
            if amt_i == 0:
                show_error()
            else:
                accf = F(acc, 2)
                q_full = accf / amt
                q_tr = _scale_value(q_full, 1, False)  # truncated, scale 1
                err = False
                if abs(q_tr) >= 10 ** 4:
                    err = True
                else:
                    quot = q_tr
                remv = accf - F(q_tr, 1) * amt
                r2 = _store(remv, 2, 7, False, True)
                if r2 is None:
                    err = True
                else:
                    rem = r2
                if err:
                    show_error()
                else:
                    out.append(acct + b" Q " + _fmt_signed(quot, 3, 1).encode() +
                               b" R " + _fmt_signed(rem, 5, 2).encode())
        else:
            out.append(acct + b" BAD OPERATION " + op)

    out.append(b"COUNT " + _fmt_unsigned(count, 4).encode() +
               b" ERRORS " + _fmt_unsigned(errors, 4).encode())
    out.append(b"FINAL " + _fmt_signed(acc, 5, 2).encode() + b" " +
               _fmt_signed(raw, 5, 2).encode() + b" " +
               _fmt_signed(binv, 4, 0).encode())

    stdout = b"".join(l + b"\n" for l in out)
    return stdout, {}

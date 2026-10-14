def _rnd(v, scale, target):
    """Round half away from zero from scale to target (target <= scale)."""
    if scale <= target:
        return v * 10 ** (target - scale)
    k = 10 ** (scale - target)
    a = abs(v)
    q, r = divmod(a, k)
    if r * 2 >= k:
        q += 1
    return q if v >= 0 else -q


def _trunc(v, scale, target):
    if scale <= target:
        return v * 10 ** (target - scale)
    k = 10 ** (scale - target)
    a = abs(v)
    q = a // k
    return q if v >= 0 else -q


def _div(v1, s1, v2, s2):
    """GnuCOBOL cob_decimal_div emulation. Returns (value, scale) or None."""
    if v2 == 0:
        return None
    if v1 == 0:
        return (0, 0)
    scale = s1 - s2
    shift = 38 + (-scale if scale < 0 else 0)
    v1 = v1 * 10 ** shift
    scale += shift
    a = abs(v1) // abs(v2)
    if (v1 < 0) != (v2 < 0):
        a = -a
    return (a, scale)


def _num(s):
    n = 0
    for ch in s:
        if '0' <= ch <= '9':
            n = n * 10 + (ord(ch) - 48)
        else:
            n = n * 10
    return n


def _store_signed(v, digits):
    m = 10 ** digits
    a = abs(v) % m
    return a if v >= 0 else -a


def _store_unsigned(v, digits):
    return abs(v) % (10 ** digits)


def _fmt_commas(cents, width, currency=False):
    ip, fp = divmod(cents, 100)
    s = "{:,}".format(ip) + "." + "%02d" % fp
    if currency:
        s = "$" + s
    return s.rjust(width)[-width:]


def _fmt_residual(cents):
    neg = cents < 0
    a = abs(cents)
    ip, fp = divmod(a, 100)
    s = str(ip) + "." + "%02d" % fp
    if neg and a != 0:
        s = "-" + s
    return s.rjust(11)


def main(stdin: bytes, input_files: dict) -> tuple:
    out = []
    data = input_files.get("LOANS.DAT", b"").decode("latin-1")
    lines = data.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    loans = 0
    errors = 0
    for line in lines:
        if line.endswith("\r"):
            line = line[:-1]
        rec = line.ljust(23)[:23]
        ln_id = rec[0:6]
        principal = _num(rec[6:15])  # scale 2
        rate = _num(rec[15:20])  # scale 3
        term = _num(rec[20:23])
        loans = (loans + 1) % 1000
        if term == 0:
            out.append(ln_id + " ERROR TERM ZERO")
            errors = (errors + 1) % 1000
            continue
        q = _div(rate, 3, 1200, 0)
        mrate = _store_unsigned(_rnd(q[0], q[1], 8), 9)  # scale 8
        if mrate == 0:
            q = _div(principal, 2, term, 0)
            payment = _store_unsigned(_rnd(q[0], q[1], 2), 9)
        else:
            factor = 10 ** 10  # scale 10
            err = False
            for _ in range(term):
                mult = 10 ** 8 + mrate  # scale 8
                prod = factor * mult  # scale 18
                r = _rnd(prod, 18, 10)
                if abs(r) >= 10 ** 19:
                    out.append(ln_id + " ERROR FACTOR OVERFLOW")
                    errors = (errors + 1) % 1000
                    err = True
                    break
                factor = abs(r)
            if err:
                continue
            num = principal * mrate * factor  # scale 20
            den = factor - 10 ** 10  # scale 10
            q = _div(num, 20, den, 10)
            if q is None:
                out.append(ln_id + " ERROR PAYMENT OVERFLOW")
                errors = (errors + 1) % 1000
                continue
            r = _rnd(q[0], q[1], 2)
            if abs(r) >= 10 ** 9:
                out.append(ln_id + " ERROR PAYMENT OVERFLOW")
                errors = (errors + 1) % 1000
                continue
            payment = abs(r)
        balance = principal  # S9(7)V99
        total_int = 0
        month = 0
        first_int = 0
        while not (balance <= 0 or month >= term):
            month += 1
            interest = _store_unsigned(_rnd(balance * mrate, 10, 2), 9)
            if month == 1:
                first_int = interest
            princ = _store_signed(payment - interest, 9)
            if princ > balance or month == term:
                princ = balance
            total_int = _store_unsigned(total_int + interest, 10)
            balance = _store_signed(balance - princ, 9)
        line_out = (ln_id + " " + _fmt_commas(payment, 13, True) + " "
                    + _fmt_commas(total_int, 13) + " "
                    + str(month % 1000).rjust(3) + " "
                    + _fmt_commas(first_int, 12) + " "
                    + _fmt_residual(balance))
        out.append(line_out)
    out.append("LOANS %03d ERRORS %03d" % (loans, errors))
    return ("\n".join(out) + "\n").encode("latin-1"), {}

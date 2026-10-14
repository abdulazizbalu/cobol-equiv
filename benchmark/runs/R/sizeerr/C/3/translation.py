from fractions import Fraction  # noqa: F401  (standard library only)


def _sign(x):
    return -1 if x < 0 else 1


def _trunc_div(a, b):
    """Integer division truncating toward zero."""
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def _round_div(a, b):
    """Integer division rounding half away from zero."""
    aa, bb = abs(a), abs(b)
    q = (2 * aa + bb) // (2 * bb)
    return q if (a < 0) == (b < 0) else -q


def _trunc_high(v, digits):
    """Drop high-order digits so the value fits in the given number of digits."""
    m = 10 ** digits
    return _sign(v) * (abs(v) % m)


def _fmt(v, intd, decd, signed=True):
    """Format a value like a GnuCOBOL DISPLAY of a numeric field."""
    total = intd + decd
    s = str(abs(v)).rjust(total, "0")[-total:]
    if decd:
        s = s[:intd] + "." + s[intd:]
    if signed:
        s = ("-" if v < 0 else "+") + s
    return s


def _parse_amount(b):
    """Read PIC S9(5)V99 DISPLAY with a trailing overpunch sign, in cents."""
    val = 0
    for c in b[:-1]:
        val = val * 10 + (c & 0x0F)
    last = b[-1]
    neg = False
    if 0x30 <= last <= 0x39 or last == 0x20:
        d = last & 0x0F
    else:
        neg = True
        d = last & 0x0F
    val = val * 10 + d
    return -val if neg else val


def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get("TXN.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    out = []
    acc = 0     # cents, max 7 digits
    raw = 0     # cents, max 7 digits
    bin_ = 0    # integer, max 4 digits
    quot = 0    # tenths, max 4 digits
    rem = 0     # cents, max 7 digits
    errors = 0
    count = 0

    def line(*parts):
        out.append(b"".join(parts) + b"\n")

    for ln in lines:
        rec = ln[:12].ljust(12, b" ")
        acct = rec[0:4]
        op = rec[4:5]
        amt = _parse_amount(rec[5:12])
        count = (count + 1) % 10000

        def show(kind):
            line(acct, kind, op, b" ", _fmt(acc, 5, 2).encode(), b" ",
                 _fmt(raw, 5, 2).encode(), b" ", _fmt(bin_, 4, 0).encode())

        def show_ok():
            show(b" OK    ")

        def show_err():
            nonlocal errors
            errors = (errors + 1) % 10000
            show(b" ERROR ")

        if op == b"A":
            r = acc + amt
            if abs(r) > 9999999:
                show_err()
            else:
                acc = r
                show_ok()
            raw = _trunc_high(raw + amt, 7)
            bin_ = _trunc_high(_trunc_div(bin_ * 100 + amt, 100), 4)
        elif op == b"S":
            r = acc - amt
            if abs(r) > 9999999:
                show_err()
            else:
                acc = r
                show_ok()
            raw = _trunc_high(raw - amt, 7)
            bin_ = _trunc_high(_trunc_div(bin_ * 100 - amt, 100), 4)
        elif op == b"M":
            r = _round_div(acc * amt, 100)
            if abs(r) > 9999999:
                show_err()
            else:
                acc = r
                show_ok()
            raw = _trunc_high(_round_div(raw * amt, 100), 7)
            bin_ = _trunc_high(_trunc_div(bin_ * amt, 100), 4)
        elif op == b"D":
            if amt == 0:
                show_err()
            else:
                r = _round_div(acc * 100, amt)
                if abs(r) > 9999999:
                    show_err()
                else:
                    acc = r
                    show_ok()
            if amt != 0:
                raw = _trunc_high(_round_div(raw * 100, amt), 7)
        elif op == b"Q":
            if amt == 0:
                show_err()
            else:
                qt = _trunc_div(acc * 10, amt)          # tenths
                rthou = acc * 10 - qt * amt             # thousandths
                rc = _trunc_div(rthou, 10)              # cents
                overflow = False
                if abs(rc) > 9999999:
                    overflow = True
                else:
                    rem = rc
                if abs(qt) > 9999:
                    overflow = True
                else:
                    quot = qt
                if overflow:
                    show_err()
                else:
                    line(acct, b" Q ", _fmt(quot, 3, 1).encode(), b" R ",
                         _fmt(rem, 5, 2).encode())
        else:
            line(acct, b" BAD OPERATION ", op)

    line(b"COUNT ", _fmt(count, 4, 0, False).encode(), b" ERRORS ",
         _fmt(errors, 4, 0, False).encode())
    line(b"FINAL ", _fmt(acc, 5, 2).encode(), b" ", _fmt(raw, 5, 2).encode(),
         b" ", _fmt(bin_, 4, 0).encode())
    return b"".join(out), {}

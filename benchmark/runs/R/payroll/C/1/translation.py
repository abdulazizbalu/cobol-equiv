from fractions import Fraction


def _parse_unsigned(bs, scale):
    v = 0
    for b in bs:
        v = v * 10 + (b & 0x0F) % 10
    return Fraction(v, 10 ** scale)


def _parse_signed_trailing(bs, scale):
    v = 0
    neg = False
    n = len(bs)
    for i, b in enumerate(bs):
        if i == n - 1:
            if 0x30 <= b <= 0x39:
                d = b - 0x30
            elif b == 0x20:
                d = 0
            elif 0x70 <= b <= 0x79:
                d = b - 0x70
                neg = True
            elif b == 0x7B:  # '{'
                d = 0
            elif 0x41 <= b <= 0x49:  # 'A'-'I'
                d = b - 0x40
            elif b == 0x7D:  # '}'
                d = 0
                neg = True
            elif 0x4A <= b <= 0x52:  # 'J'-'R'
                d = b - 0x49
                neg = True
            else:
                d = (b & 0x0F) % 10
                neg = True
        else:
            d = (b & 0x0F) % 10
        v = v * 10 + d
    f = Fraction(v, 10 ** scale)
    return -f if neg else f


def _trunc_int(x):
    # truncate toward zero
    if x >= 0:
        return x.numerator // x.denominator
    return -((-x.numerator) // x.denominator)


def _store(value, scale, digits, rounded=False):
    """Return scaled integer stored into a field with given scale/digits."""
    x = Fraction(value) * (10 ** scale)
    if rounded:
        if x >= 0:
            n = _trunc_int(x + Fraction(1, 2))
        else:
            n = -_trunc_int(-x + Fraction(1, 2))
    else:
        n = _trunc_int(x)
    mod = 10 ** digits
    if n >= 0:
        n = n % mod
    else:
        n = -((-n) % mod)
    return n


def _val(n, scale):
    return Fraction(n, 10 ** scale)


def _disp_signed(n, int_digits, scale):
    s = "+" if n >= 0 else "-"
    a = abs(n)
    digs = str(a).zfill(int_digits + scale)
    if scale:
        return s + digs[:int_digits] + "." + digs[int_digits:]
    return s + digs


def _disp_unsigned(n, digits):
    return str(abs(n)).zfill(digits)


def _packed(n, digits):
    a = abs(n) % (10 ** digits)
    ds = str(a).zfill(digits)
    nibbles = [int(c) for c in ds] + [0x0D if n < 0 else 0x0C]
    if len(nibbles) % 2:
        nibbles = [0] + nibbles
    out = bytearray()
    for i in range(0, len(nibbles), 2):
        out.append((nibbles[i] << 4) | nibbles[i + 1])
    return bytes(out)


def _display_signed_field(n, digits):
    a = abs(n) % (10 ** digits)
    ds = str(a).zfill(digits)
    if n < 0:
        last = chr(0x70 + int(ds[-1]))
    else:
        last = ds[-1]
    return (ds[:-1] + last).encode("latin-1")


def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get("EMPLOYEES.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    out = []
    pay = bytearray()

    tot_gross = 0  # scale 2, 11 digits
    tot_net = 0
    neg_count = 0
    emp_count = 0

    for line in lines:
        rec = line[:32].ljust(32, b" ")
        emp_id = rec[0:5]
        emp_name = rec[5:15]
        hours = _parse_unsigned(rec[15:19], 1)
        rate = _parse_unsigned(rec[19:24], 2)
        ded_code = rec[24:25]
        adjust = _parse_signed_trailing(rec[25:32], 2)

        emp_count = (emp_count + 1) % 1000

        if hours > 40:
            ot = _store(hours - 40, 1, 4)
            otv = _val(ot, 1)
            gross = _store(40 * rate + otv * rate * Fraction(3, 2), 2, 9, True)
        else:
            ot = 0
            gross = _store(hours * rate, 2, 9, True)
        g = _val(gross, 2)

        if g <= 1000:
            tax = _store(g * Fraction(1, 10), 2, 9, True)
        elif g <= 5000:
            tax = _store(100 + (g - 1000) * Fraction(1, 4), 2, 9, True)
        else:
            tax = _store(1100 + (g - 5000) * Fraction(35, 100), 2, 9, True)
        t = _val(tax, 2)

        if ded_code == b"A":
            ded = _store(50, 2, 7)
        elif ded_code == b"B":
            ded = _store(g * Fraction(45, 1000), 2, 7, True)
        elif ded_code == b"C":
            ded = 0
        else:
            ded = _store(Fraction(2550, 100), 2, 7)
        d = _val(ded, 2)

        net = _store(g - t - d + adjust, 2, 9)

        flag = b" "
        if net < 0:
            neg_count = (neg_count + 1) % 1000
            flag = b"N"

        tot_gross = _store(_val(tot_gross, 2) + g, 2, 11)
        tot_net = _store(_val(tot_net, 2) + _val(net, 2), 2, 11)

        pay += emp_id
        pay += _packed(gross, 9)
        pay += _packed(net, 9)
        pay += _display_signed_field(net, 9)
        pay += flag

        line_out = (emp_id + b" " + emp_name + b" "
                    + _disp_signed(gross, 7, 2).encode() + b" "
                    + _disp_signed(tax, 7, 2).encode() + b" "
                    + _disp_signed(ded, 5, 2).encode() + b" "
                    + _disp_signed(net, 7, 2).encode() + b"\n")
        out.append(line_out)

    out.append(("EMPLOYEES " + _disp_unsigned(emp_count, 3) + "\n").encode())
    out.append(("TOTAL GROSS " + _disp_signed(tot_gross, 9, 2) + "\n").encode())
    out.append(("TOTAL NET   " + _disp_signed(tot_net, 9, 2) + "\n").encode())
    out.append(("NEGATIVE NET " + _disp_unsigned(neg_count, 3) + "\n").encode())

    return b"".join(out), {"PAYOUT.DAT": bytes(pay)}

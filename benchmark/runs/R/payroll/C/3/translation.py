from fractions import Fraction


def _digit(c):
    return c & 0x0F


def _parse_unsigned(b):
    v = 0
    for c in b:
        v = v * 10 + (_digit(c) % 10)
    return v


def _parse_signed_trailing(b):
    v = 0
    neg = False
    n = len(b)
    for i, c in enumerate(b):
        if i == n - 1:
            if 0x30 <= c <= 0x39:
                d = c - 0x30
            elif c == 0x20:
                d = 0
            else:
                neg = True
                d = (c - 0x40) & 0x0F if c >= 0x40 else c & 0x0F
                d %= 10
        else:
            d = _digit(c) % 10
        v = v * 10 + d
    return -v if neg else v


def _round_half_away(fr):
    # fr is a Fraction; round half away from zero to integer
    if fr >= 0:
        return int((fr + Fraction(1, 2)).__floor__())
    else:
        return -int((-fr + Fraction(1, 2)).__floor__())


def _trunc_int(fr):
    if fr >= 0:
        return int(fr.__floor__())
    return -int((-fr).__floor__())


def _store(v, digits, signed=True):
    m = 10 ** digits
    if v < 0:
        r = -((-v) % m)
    else:
        r = v % m
    if not signed:
        r = abs(r)
    return r


def _disp_signed(v, int_digits, dec_digits):
    s = "-" if v < 0 else "+"
    a = abs(v)
    total = int_digits + dec_digits
    ds = str(a).zfill(total)
    if dec_digits:
        return s + ds[:int_digits] + "." + ds[int_digits:]
    return s + ds


def _comp3(v, digits, signed=True):
    a = abs(v)
    ds = str(a).zfill(digits)
    if digits % 2 == 0:
        ds = "0" + ds
    if not signed:
        sign = 0x0F
    else:
        sign = 0x0D if v < 0 else 0x0C
    nibbles = [int(ch) for ch in ds] + [sign]
    out = bytearray()
    for i in range(0, len(nibbles), 2):
        out.append((nibbles[i] << 4) | nibbles[i + 1])
    return bytes(out)


def _display_trailing(v, digits):
    a = abs(v)
    ds = bytearray(str(a).zfill(digits).encode())
    if v < 0:
        ds[-1] = ds[-1] + 0x40
    return bytes(ds)


def main(stdin, input_files):
    data = input_files.get("EMPLOYEES.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    out = []
    payout = bytearray()

    tot_gross = 0
    tot_net = 0
    neg_count = 0
    emp_count = 0

    for line in lines:
        rec = line[:32].ljust(32, b" ")
        emp_id = rec[0:5]
        emp_name = rec[5:15]
        hours_t = _parse_unsigned(rec[15:19])  # tenths
        rate_c = _parse_unsigned(rec[19:24])  # cents
        ded_code = rec[24:25]
        adj_c = _parse_signed_trailing(rec[25:32])  # cents

        emp_count = _store(emp_count + 1, 3, signed=False)

        if hours_t > 400:
            ot_t = _store(hours_t - 400, 4)
            # gross in cents
            g = Fraction(40 * rate_c) + Fraction(ot_t, 10) * rate_c * Fraction(3, 2)
            gross = _store(_round_half_away(g), 9)
        else:
            ot_t = 0
            g = Fraction(hours_t * rate_c, 10)
            gross = _store(_round_half_away(g), 9)

        if gross <= 100000:
            tax = _round_half_away(Fraction(gross) * Fraction(1, 10))
        elif gross <= 500000:
            tax = _round_half_away(10000 + Fraction(gross - 100000) * Fraction(1, 4))
        else:
            tax = _round_half_away(110000 + Fraction(gross - 500000) * Fraction(35, 100))
        tax = _store(tax, 9)

        if ded_code == b"A":
            ded = 5000
        elif ded_code == b"B":
            ded = _store(_round_half_away(Fraction(gross) * Fraction(45, 1000)), 7)
        elif ded_code == b"C":
            ded = 0
        else:
            ded = 2550

        net = _store(gross - tax - ded + adj_c, 9)
        flag = b" "
        if net < 0:
            neg_count = _store(neg_count + 1, 3, signed=False)
            flag = b"N"
        tot_gross = _store(tot_gross + gross, 11)
        tot_net = _store(tot_net + net, 11)

        payout += emp_id + _comp3(gross, 9) + _comp3(net, 9) + _display_trailing(net, 9) + flag

        out.append(
            emp_id + b" " + emp_name + b" "
            + _disp_signed(gross, 7, 2).encode() + b" "
            + _disp_signed(tax, 7, 2).encode() + b" "
            + _disp_signed(ded, 5, 2).encode() + b" "
            + _disp_signed(net, 7, 2).encode() + b"\n"
        )

    out.append(b"EMPLOYEES " + str(emp_count).zfill(3).encode() + b"\n")
    out.append(b"TOTAL GROSS " + _disp_signed(tot_gross, 9, 2).encode() + b"\n")
    out.append(b"TOTAL NET   " + _disp_signed(tot_net, 9, 2).encode() + b"\n")
    out.append(b"NEGATIVE NET " + str(neg_count).zfill(3).encode() + b"\n")

    return b"".join(out), {"PAYOUT.DAT": bytes(payout)}

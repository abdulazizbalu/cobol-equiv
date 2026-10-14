from fractions import Fraction


def _round_half_away(x: Fraction, places: int) -> Fraction:
    scale = 10 ** places
    v = x * scale
    sign = -1 if v < 0 else 1
    a = abs(v)
    n = a.numerator // a.denominator
    rem = a - n
    if rem * 2 >= 1:
        n += 1
    return Fraction(sign * n, scale)


def _trunc(x: Fraction, places: int) -> Fraction:
    scale = 10 ** places
    v = x * scale
    sign = -1 if v < 0 else 1
    a = abs(v)
    n = a.numerator // a.denominator
    return Fraction(sign * n, scale)


def _mod_store(x: Fraction, int_digits: int, places: int, signed: bool) -> Fraction:
    x = _trunc(x, places)
    scale = 10 ** places
    cents = int(x * scale)
    sign = -1 if cents < 0 else 1
    a = abs(cents) % (10 ** (int_digits + places))
    if not signed:
        sign = 1
    return Fraction(sign * a, scale)


def _num(s: str, places: int) -> Fraction:
    digits = "".join(c if c.isdigit() else "0" for c in s)
    return Fraction(int(digits or "0"), 10 ** places)


def _fmt_cents(v: Fraction):
    cents = int(abs(v) * 100)
    return cents // 100, cents % 100


def _ed_dollar(v: Fraction) -> str:
    i, f = _fmt_cents(v)
    return ("$" + f"{i:,}" + ".%02d" % f).rjust(13)


def _ed_z(v: Fraction, width: int) -> str:
    i, f = _fmt_cents(v)
    return (f"{i:,}" + ".%02d" % f).rjust(width)


def _ed_minus(v: Fraction) -> str:
    i, f = _fmt_cents(v)
    s = "%d.%02d" % (i, f)
    if v < 0 and (i or f):
        s = "-" + s
    return s.rjust(11)


def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get("LOANS.DAT", b"").decode("latin-1")
    lines = data.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    out = []
    loans = 0
    errors = 0

    for line in lines:
        rec = line[:23].ljust(23)
        ln_id = rec[0:6]
        principal = _num(rec[6:15], 2)
        rate = _num(rec[15:20], 3)
        term = int("".join(c if c.isdigit() else "0" for c in rec[20:23]))

        loans = (loans + 1) % 1000
        if term == 0:
            out.append(ln_id + " ERROR TERM ZERO")
            errors = (errors + 1) % 1000
            continue
        mrate = _round_half_away(rate / 1200, 8)
        if mrate == 0:
            payment = _round_half_away(principal / term, 2)
            payment = _mod_store(payment, 7, 2, False)
        else:
            factor = Fraction(1)
            err = False
            for _ in range(term):
                nf = _round_half_away(factor * (1 + mrate), 10)
                if abs(nf) >= 10 ** 9:
                    err = True
                    break
                factor = nf
            if err:
                out.append(ln_id + " ERROR FACTOR OVERFLOW")
                errors = (errors + 1) % 1000
                continue
            den = factor - 1
            if den == 0:
                out.append(ln_id + " ERROR PAYMENT OVERFLOW")
                errors = (errors + 1) % 1000
                continue
            p = _round_half_away(principal * mrate * factor / den, 2)
            if abs(p) >= 10 ** 7:
                out.append(ln_id + " ERROR PAYMENT OVERFLOW")
                errors = (errors + 1) % 1000
                continue
            payment = abs(p)

        balance = _mod_store(principal, 7, 2, True)
        total_int = Fraction(0)
        month = 0
        first_int = Fraction(0)
        while not (balance <= 0 or month >= term):
            month = (month + 1) % 1000
            interest = _mod_store(_round_half_away(balance * mrate, 2), 7, 2, False)
            if month == 1:
                first_int = interest
            princ = _mod_store(payment - interest, 7, 2, True)
            if princ > balance or month == term:
                princ = balance
            total_int = _mod_store(total_int + interest, 8, 2, False)
            balance = _mod_store(balance - princ, 7, 2, True)

        s = (ln_id + " " + _ed_dollar(payment) + " " + _ed_z(total_int, 13)
             + " " + str(month).rjust(3) + " " + _ed_z(first_int, 12)
             + " " + _ed_minus(balance))
        out.append(s)

    out.append("LOANS %03d ERRORS %03d" % (loans, errors))
    stdout = ("\n".join(out) + "\n").encode("latin-1")
    return stdout, {}

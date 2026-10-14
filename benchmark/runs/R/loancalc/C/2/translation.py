def _num(s):
    v = 0
    for ch in s:
        v = v * 10 + (ord(ch) & 0x0F) % 10
    return v


def _commas(n):
    return "{:,}".format(n)


def _fmt_payment(v):
    ip, fp = divmod(v, 100)
    return ("$" + _commas(ip)).rjust(10) + "." + "%02d" % fp


def _fmt_z(v, width):
    ip, fp = divmod(v, 100)
    return _commas(ip).rjust(width) + "." + "%02d" % fp


def _fmt_residual(v):
    neg = v < 0
    a = -v if neg else v
    ip, fp = divmod(a, 100)
    s = ("-" if neg else "") + str(ip)
    return s.rjust(8) + "." + "%02d" % fp


def _trunc_signed(v, mod):
    if v < 0:
        return -((-v) % mod)
    return v % mod


def main(stdin, input_files):
    data = input_files.get("LOANS.DAT", b"")
    text = data.decode("latin-1")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()

    out = []
    loans = 0
    errors = 0
    mrate = 0
    factor = 0
    payment = 0
    balance = 0
    interest = 0
    total_int = 0
    month = 0
    first_int = 0

    for line in lines:
        if line.endswith("\r"):
            line = line[:-1]
        rec = line[:23].ljust(23)
        ln_id = rec[0:6]
        principal = _num(rec[6:15])
        rate = _num(rec[15:20])
        term = _num(rec[20:23])

        loans = (loans + 1) % 1000
        if term == 0:
            out.append(ln_id + " ERROR TERM ZERO")
            errors = (errors + 1) % 1000
            continue

        # mrate scale 8: rate (scale 3) / 1200
        x = rate * 1000000 // 1200  # scale 9
        mrate = ((x + 5) // 10) % 10**9

        err = False
        if mrate == 0:
            x = principal * 10 // term  # scale 3
            payment = ((x + 5) // 10) % 10**9
        else:
            factor = 10**10
            mult = 10**8 + mrate
            for _ in range(term):
                prod = factor * mult  # scale 18
                x = prod // 10**7  # scale 11
                r = (x + 5) // 10
                if r >= 10**19:
                    out.append(ln_id + " ERROR FACTOR OVERFLOW")
                    errors = (errors + 1) % 1000
                    err = True
                    break
                factor = r
            if err:
                continue
            N = principal * mrate * factor  # scale 20
            D = factor - 10**10  # scale 10
            if D == 0:
                out.append(ln_id + " ERROR PAYMENT OVERFLOW")
                errors = (errors + 1) % 1000
                continue
            neg = (N < 0) != (D < 0)
            q = abs(N) // (abs(D) * 10**7)  # scale 3
            r = (q + 5) // 10
            if r >= 10**9:
                out.append(ln_id + " ERROR PAYMENT OVERFLOW")
                errors = (errors + 1) % 1000
                continue
            payment = r  # unsigned field

        balance = principal
        total_int = 0
        month = 0
        first_int = 0
        while not (balance <= 0 or month >= term):
            month = (month + 1) % 1000
            prod = balance * mrate  # scale 10
            if prod >= 0:
                x = prod // 10**7
                interest = ((x + 5) // 10)
            else:
                x = (-prod) // 10**7
                interest = ((x + 5) // 10)
            interest = interest % 10**9
            if month == 1:
                first_int = interest
            pp = _trunc_signed(payment - interest, 10**9)
            if pp > balance or month == term:
                pp = balance
            total_int = (total_int + interest) % 10**10
            balance = _trunc_signed(balance - pp, 10**9)

        line_out = (ln_id + " " + _fmt_payment(payment) + " "
                    + _fmt_z(total_int, 10) + " "
                    + str(month).rjust(3) + " "
                    + _fmt_z(first_int, 9) + " "
                    + _fmt_residual(balance))
        out.append(line_out)

    out.append("LOANS %03d ERRORS %03d" % (loans, errors))
    stdout = ("\n".join(out) + "\n").encode("latin-1")
    return stdout, {}

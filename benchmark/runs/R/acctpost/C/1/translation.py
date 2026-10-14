def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get("TXNS.DAT", b"")
    text = data.decode("latin-1")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()

    out = []
    accounts = []  # list of [id, bal_cents, ntx]
    errors = 0
    BAL_MOD = 10 ** 9

    def trunc_bal(v):
        s = -1 if v < 0 else 1
        r = abs(v) % BAL_MOD
        return s * r

    def fmt_amt(cents):
        cents = abs(cents) % 10000000
        ip = cents // 100
        fp = cents % 100
        return str(ip).rjust(5) + "." + "%02d" % fp

    def fmt_bal(cents):
        neg = cents < 0
        c = abs(cents) % BAL_MOD
        ip = c // 100
        fp = c % 100
        s = str(ip)
        if neg and c != 0:
            s = "-" + s
        return s.rjust(8) + "." + "%02d" % fp

    def num(s):
        r = 0
        for ch in s:
            if ch.isdigit():
                r = r * 10 + int(ch)
            else:
                r = r * 10 + (ord(ch) & 0x0F) % 10
        return r

    for line in lines:
        rec = line[:12].ljust(12)
        acct = rec[0:4]
        type_ch = rec[4]
        ttype = num(type_ch)
        amt = num(rec[5:12])

        def reject(msg):
            nonlocal errors
            errors = (errors + 1) % 1000
            out.append("REJECT " + acct + " " + type_ch + " " + fmt_amt(amt)
                       + " " + msg[:20].ljust(20))

        if acct == "    ":
            reject("NO ACCOUNT")
            continue
        k = 0
        for idx, a in enumerate(accounts):
            if a[0] == acct:
                k = idx + 1
                break
        if k == 0 and len(accounts) < 5:
            accounts.append([acct, 0, 0])
            k = len(accounts)
        if k == 0:
            reject("TOO MANY ACCOUNTS")
            continue
        a = accounts[k - 1]
        if ttype == 1:
            a[1] = trunc_bal(a[1] + amt)
            a[2] = (a[2] + 1) % 1000
        elif ttype == 2:
            if amt > a[1]:
                reject("INSUFFICIENT FUNDS")
                continue
            a[1] = trunc_bal(a[1] - amt)
            a[2] = (a[2] + 1) % 1000
        elif ttype == 3:
            fee = (15 * amt + 25000 + 500) // 1000
            fee = fee % 100000
            a[1] = trunc_bal(a[1] - fee)
            out.append("FEE " + acct + " " + fmt_amt(fee))
            a[2] = (a[2] + 1) % 1000
        else:
            reject("BAD TYPE")

    for a in accounts:
        out.append(a[0] + " " + fmt_bal(a[1]) + " " + "%03d" % a[2])
    out.append("ERRORS " + "%03d" % errors)
    res = "".join(l + "\n" for l in out)
    return res.encode("latin-1"), {}

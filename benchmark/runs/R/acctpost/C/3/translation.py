def _num(bs):
    v = 0
    for c in bs:
        v = v * 10 + ((c & 0x0F) % 10)
    return v


def _fmt_amt(cents):
    # PIC Z(4)9.99
    cents = abs(cents) % 10000000
    ip, fp = divmod(cents, 100)
    return (str(ip).rjust(5) + "." + "%02d" % fp).encode()


def _fmt_bal(cents):
    # PIC -(7)9.99
    neg = cents < 0
    a = abs(cents)
    ip, fp = divmod(a, 100)
    s = str(ip)
    if neg and a != 0:
        s = "-" + s
    return (s.rjust(8) + "." + "%02d" % fp).encode()


def _trunc_signed(v, mod):
    if v < 0:
        return -((-v) % mod)
    return v % mod


def main(stdin, input_files):
    data = input_files.get("TXNS.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    out = []
    acc_ids = []
    bals = []
    ntx = []
    errors = 0

    for line in lines:
        rec = line[:12].ljust(12, b" ")
        acct = rec[0:4]
        ttype_b = rec[4:5]
        amt = _num(rec[5:12])
        ttype = _num(ttype_b)

        msg = None
        if acct == b"    ":
            msg = b"NO ACCOUNT"
        else:
            k = 0
            for i in range(len(acc_ids)):
                if acc_ids[i] == acct:
                    k = i + 1
                    break
            if k == 0 and len(acc_ids) < 5:
                acc_ids.append(acct)
                bals.append(0)
                ntx.append(0)
                k = len(acc_ids)
            if k == 0:
                msg = b"TOO MANY ACCOUNTS"
            else:
                idx = k - 1
                if ttype == 1:
                    bals[idx] = _trunc_signed(bals[idx] + amt, 10 ** 9)
                    ntx[idx] = (ntx[idx] + 1) % 1000
                elif ttype == 2:
                    if amt > bals[idx]:
                        msg = b"INSUFFICIENT FUNDS"
                    else:
                        bals[idx] = _trunc_signed(bals[idx] - amt, 10 ** 9)
                        ntx[idx] = (ntx[idx] + 1) % 1000
                elif ttype == 3:
                    x = amt * 15 + 25000
                    fee = ((x + 500) // 1000) % 100000
                    bals[idx] = _trunc_signed(bals[idx] - fee, 10 ** 9)
                    out.append(b"FEE " + acct + b" " + _fmt_amt(fee) + b"\n")
                    ntx[idx] = (ntx[idx] + 1) % 1000
                else:
                    msg = b"BAD TYPE"
        if msg is not None:
            errors = (errors + 1) % 1000
            out.append(b"REJECT " + acct + b" " + ttype_b + b" " + _fmt_amt(amt)
                       + b" " + msg.ljust(20, b" ")[:20] + b"\n")

    for i in range(len(acc_ids)):
        out.append(acc_ids[i] + b" " + _fmt_bal(bals[i]) + b" "
                   + ("%03d" % ntx[i]).encode() + b"\n")
    out.append(b"ERRORS " + ("%03d" % errors).encode() + b"\n")
    return b"".join(out), {}

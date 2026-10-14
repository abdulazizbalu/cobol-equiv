def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get('TXNS.DAT', b'').decode('latin-1')
    lines = data.split('\n')
    if lines and lines[-1] == '':
        lines.pop()

    out = []

    def numval(s):
        v = 0
        for ch in s:
            if '0' <= ch <= '9':
                d = ord(ch) - 48
            elif ch == ' ':
                d = 0
            else:
                d = ord(ch) & 0x0F
                if d > 9:
                    d = d % 10
            v = v * 10 + d
        return v

    def fmt_amt(cents):
        # Z(4)9.99
        cents = abs(cents) % 10000000
        ip, fp = divmod(cents, 100)
        return str(ip).rjust(5) + '.' + '%02d' % fp

    def fmt_bal(cents):
        # -(7)9.99
        neg = cents < 0
        c = abs(cents) % 1000000000
        ip, fp = divmod(c, 100)
        s = str(ip)
        if neg and c != 0:
            s = '-' + s
        return s.rjust(8)[-8:] + '.' + '%02d' % fp

    def trunc_signed(v, mod):
        neg = v < 0
        a = abs(v) % mod
        return -a if neg else a

    acc_ids = [''] * 6
    bal = [0] * 6
    ntx = [0] * 6
    nacc = 0
    errors = 0

    for line in lines:
        rec = line[:12].ljust(12)
        tx_acct = rec[0:4]
        tx_type_c = rec[4]
        tx_type = numval(tx_type_c)
        tx_amt = numval(rec[5:12])

        msg = None
        if tx_acct == '    ':
            msg = 'NO ACCOUNT'
        else:
            k = 0
            i = 1
            while not (i > nacc or k > 0):
                if acc_ids[i] == tx_acct:
                    k = i
                i += 1
            if k == 0 and nacc < 5:
                nacc += 1
                k = nacc
                acc_ids[k] = tx_acct
                bal[k] = 0
                ntx[k] = 0
            if k == 0:
                msg = 'TOO MANY ACCOUNTS'
            else:
                if tx_type == 1:
                    bal[k] = trunc_signed(bal[k] + tx_amt, 1000000000)
                    ntx[k] = (ntx[k] + 1) % 1000
                elif tx_type == 2:
                    if tx_amt > bal[k]:
                        msg = 'INSUFFICIENT FUNDS'
                    else:
                        bal[k] = trunc_signed(bal[k] - tx_amt, 1000000000)
                        ntx[k] = (ntx[k] + 1) % 1000
                elif tx_type == 3:
                    # tx_amt in cents; fee = amt*0.015 + 0.25, exact in 1/100000 units
                    exact = tx_amt * 15 + 25000  # units of 1e-5 (cents*1000)
                    fee = (exact + 500) // 1000
                    fee %= 100000
                    bal[k] = trunc_signed(bal[k] - fee, 1000000000)
                    out.append('FEE ' + tx_acct + ' ' + fmt_amt(fee))
                    ntx[k] = (ntx[k] + 1) % 1000
                else:
                    msg = 'BAD TYPE'
        if msg is not None:
            errors = (errors + 1) % 1000
            out.append('REJECT ' + tx_acct + ' ' + tx_type_c + ' ' +
                       fmt_amt(tx_amt) + ' ' + msg.ljust(20)[:20])

    for i in range(1, nacc + 1):
        out.append(acc_ids[i] + ' ' + fmt_bal(bal[i]) + ' ' + '%03d' % ntx[i])
    out.append('ERRORS ' + '%03d' % errors)

    stdout = ''.join(s + '\n' for s in out).encode('latin-1')
    return stdout, {}

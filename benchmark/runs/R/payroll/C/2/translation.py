def _round_div(n, d):
    s = -1 if n < 0 else 1
    q, r = divmod(abs(n), d)
    if 2 * r >= d:
        q += 1
    return s * q


def _trunc_mod(n, digits):
    s = -1 if n < 0 else 1
    v = abs(n) % (10 ** digits)
    return s * v if v else 0


def _unsigned(b):
    v = 0
    for c in b:
        v = v * 10 + (c & 0x0F)
    return v


def _signed_trailing(b):
    v = 0
    for c in b[:-1]:
        v = v * 10 + (c & 0x0F)
    c = b[-1]
    neg = False
    if 0x70 <= c <= 0x79:
        d = c - 0x70
        neg = True
    elif c == ord('}'):
        d = 0
        neg = True
    elif ord('J') <= c <= ord('R'):
        d = c - ord('J') + 1
        neg = True
    elif c == ord('{'):
        d = 0
    elif ord('A') <= c <= ord('I'):
        d = c - ord('A') + 1
    else:
        d = c & 0x0F
    v = v * 10 + d
    return -v if neg else v


def _packed(v, digits, signed=True):
    s = str(abs(v)).rjust(digits, '0')[-digits:]
    if signed:
        sign = 'd' if v < 0 else 'c'
    else:
        sign = 'f'
    h = s + sign
    if len(h) % 2:
        h = '0' + h
    return bytes.fromhex(h)


def _disp_signed(v, intd, decd):
    s = str(abs(v)).rjust(intd + decd, '0')
    sign = '-' if v < 0 else '+'
    if decd:
        return sign + s[:intd] + '.' + s[intd:]
    return sign + s


def _zoned_signed(v, digits):
    s = str(abs(v)).rjust(digits, '0')[-digits:]
    if v < 0:
        return (s[:-1] + chr(0x70 + int(s[-1]))).encode('latin-1')
    return s.encode('latin-1')


def main(stdin, input_files):
    data = input_files.get('EMPLOYEES.DAT', b'')
    lines = data.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
    out = []
    pay = bytearray()
    tot_gross = 0
    tot_net = 0
    neg_count = 0
    emp_count = 0
    for line in lines:
        rec = line[:32].ljust(32, b' ')
        emp_id = rec[0:5]
        emp_name = rec[5:15]
        hours = _unsigned(rec[15:19])      # scale 1
        rate = _unsigned(rec[19:24])       # scale 2
        ded_code = rec[24:25]
        adjust = _signed_trailing(rec[25:32])  # scale 2

        emp_count = (emp_count + 1) % 1000
        if hours > 400:
            ot = _trunc_mod(hours - 400, 4)
            g4 = 40 * rate * 100 + ot * rate * 15
            gross = _trunc_mod(_round_div(g4, 100), 9)
        else:
            ot = 0
            g3 = hours * rate
            gross = _trunc_mod(_round_div(g3, 10), 9)

        if gross <= 100000:
            tax = _round_div(gross * 10, 10)
        elif gross <= 500000:
            tax = _round_div(1000000 + (gross - 100000) * 25, 100)
        else:
            tax = _round_div(11000000 + (gross - 500000) * 35, 100)
        tax = _trunc_mod(tax, 9)

        if ded_code == b'A':
            ded = 5000
        elif ded_code == b'B':
            ded = _trunc_mod(_round_div(gross * 45, 1000), 7)
        elif ded_code == b'C':
            ded = 0
        else:
            ded = 2550

        net = _trunc_mod(gross - tax - ded + adjust, 9)
        flag = b' '
        if net < 0:
            neg_count = (neg_count + 1) % 1000
            flag = b'N'
        tot_gross = _trunc_mod(tot_gross + gross, 11)
        tot_net = _trunc_mod(tot_net + net, 11)

        pay += emp_id + _packed(gross, 9) + _packed(net, 9) + _zoned_signed(net, 9) + flag

        out.append(emp_id + b' ' + emp_name + b' ' +
                   _disp_signed(gross, 7, 2).encode() + b' ' +
                   _disp_signed(tax, 7, 2).encode() + b' ' +
                   _disp_signed(ded, 5, 2).encode() + b' ' +
                   _disp_signed(net, 7, 2).encode() + b'\n')

    out.append(b'EMPLOYEES ' + str(emp_count).rjust(3, '0').encode() + b'\n')
    out.append(b'TOTAL GROSS ' + _disp_signed(tot_gross, 9, 2).encode() + b'\n')
    out.append(b'TOTAL NET   ' + _disp_signed(tot_net, 9, 2).encode() + b'\n')
    out.append(b'NEGATIVE NET ' + str(neg_count).rjust(3, '0').encode() + b'\n')
    return b''.join(out), {'PAYOUT.DAT': bytes(pay)}

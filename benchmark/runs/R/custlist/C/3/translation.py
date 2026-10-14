def _dig(c):
    return ord(c) & 0x0F


def _num_unsigned(s):
    v = 0
    for c in s:
        v = v * 10 + _dig(c)
    return v


def _signed_parts(s):
    """Return (negative, digit_chars) for trailing embedded sign display field."""
    last = s[-1]
    o = ord(last)
    neg = False
    if 0x70 <= o <= 0x79:
        neg = True
        last = chr(o - 0x40)
    return neg, s[:-1] + last


def _zedit(s):
    # Z...Z9 editing using raw characters
    out = []
    suppress = True
    n = len(s)
    for i, c in enumerate(s):
        if i == n - 1:
            out.append(c)
            continue
        if c != '0':
            suppress = False
        out.append(' ' if suppress else c)
    return ''.join(out)


def _float_minus(int_digits, dec_digits, neg):
    # int_digits: string of n chars, edit pattern -(n)9 style with sign floating
    is_zero = all(c == '0' for c in int_digits + dec_digits)
    if is_zero:
        neg = False
    n = len(int_digits)
    i = 0
    while i < n - 1 and int_digits[i] == '0':
        i += 1
    sign = '-' if neg else ' '
    return ' ' * i + sign + int_digits[i:] + '.' + dec_digits


def main(stdin, input_files):
    data = input_files.get('CUST.DAT', b'').decode('latin-1')
    lines = data.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    out_lines = []
    stdout = []
    count = 0
    total = 0  # in cents
    for line in lines:
        rec = line[:64].ljust(64)
        cu_id = rec[0:5]
        cu_last = rec[5:15]
        cu_first = rec[15:23]
        cu_house = rec[23:27]
        cu_road = rec[27:39]
        cu_city = rec[39:49]
        cu_yyyy = rec[49:53]
        cu_mm = rec[53:55]
        cu_dd = rec[55:57]
        cu_opened = rec[49:57]
        cu_bal = rec[57:64]

        count = (count + 1) % 1000
        neg, bdig = _signed_parts(cu_bal)
        bval = _num_unsigned(bdig)
        if neg:
            bval = -bval
        total += bval
        if total >= 10 ** 9 or total <= -10 ** 9:
            s = -1 if total < 0 else 1
            total = s * (abs(total) % 10 ** 9)

        mm = _num_unsigned(cu_mm)
        if mm < 1 or mm > 12:
            flag = ' BADM'
        elif _num_unsigned(cu_opened) < 19000101:
            flag = ' OLD'
        else:
            flag = ''
        flag = flag.ljust(5)

        bal_ed = _float_minus(bdig[:5], bdig[5:7], neg)

        wo = (_zedit(cu_id) + '|' + cu_first + ' ' + cu_last + '|' +
              cu_city + ',' + _zedit(cu_house) + ' ' + cu_road + '|' +
              cu_dd + '/' + cu_mm + '/' + cu_yyyy + '|' + bal_ed + flag)
        out_lines.append(wo.rstrip(' ') + '\n')

        if cu_last == ' ' * 10:
            name_copy = (cu_last + cu_first).ljust(20)
            stdout.append('NO LAST NAME ' + cu_id + ' [' + name_copy + ']\n')

    tneg = total < 0
    a = abs(total)
    ip = '%07d' % (a // 100)
    dp = '%02d' % (a % 100)
    tot_ed = _float_minus(ip, dp, tneg)
    stdout.append('COUNT ' + '%03d' % count + ' TOTAL ' + tot_ed + '\n')

    return (''.join(stdout).encode('latin-1'),
            {'CUSTLIST.DAT': ''.join(out_lines).encode('latin-1')})

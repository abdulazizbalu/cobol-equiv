def _edit(digits, scale, neg, pic):
    # digits: string of source digit characters, scale: number of decimals
    src_int = len(digits) - scale
    # count destination integer digit positions
    if '.' in pic:
        ip, fp = pic.split('.', 1)
    else:
        ip, fp = pic, ''
    dest_int = 0
    first = True
    for c in ip:
        if c in '9Z':
            dest_int += 1
        elif c == '-':
            if first:
                first = False
            else:
                dest_int += 1
    # build digit stream
    stream = []
    for k in range(dest_int):
        idx = src_int - dest_int + k
        stream.append(digits[idx] if 0 <= idx < src_int else '0')
    nfrac = sum(1 for c in fp if c in '9Z')
    for k in range(nfrac):
        idx = src_int + k
        stream.append(digits[idx] if idx < len(digits) else '0')
    it = iter(stream)

    suppress = True
    is_zero = True
    sign_pos = None
    first_sign = True
    out = []
    for c in pic:
        if c == '9':
            x = next(it)
            if x != '0':
                is_zero = False
            suppress = False
            out.append(x)
        elif c == 'Z':
            x = next(it)
            if x != '0':
                is_zero = False
                suppress = False
            out.append(' ' if suppress else x)
        elif c == '-':
            if first_sign:
                first_sign = False
                sign_pos = len(out)
                out.append(' ')
            else:
                x = next(it)
                if x != '0':
                    is_zero = False
                    suppress = False
                if suppress:
                    sign_pos = len(out)
                    out.append(' ')
                else:
                    out.append(x)
        elif c == '.':
            out.append(' ' if suppress else '.')
        else:
            out.append(c)
    if sign_pos is not None and neg and not is_zero:
        out[sign_pos] = '-'
    return ''.join(out)


def _unpunch(s):
    # trailing overpunch sign (ASCII convention)
    last = s[-1]
    o = ord(last)
    if 0x70 <= o <= 0x79:
        return s[:-1] + chr(o - 0x40), True
    return s, False


def _numval(s):
    n = 0
    for ch in s:
        n = n * 10 + (ord(ch) & 0x0F)
    return n


def main(stdin, input_files):
    data = input_files.get('CUST.DAT', b'')
    text = data.decode('latin-1')
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    RECLEN = 64
    out_stdout = []
    out_file = []
    count = 0
    total = 0  # in cents
    for line in lines:
        rec = line[:RECLEN].ljust(RECLEN)
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
        bal_digits, bal_neg = _unpunch(cu_bal)
        bv = _numval(bal_digits)
        if bal_neg:
            bv = -bv
        total = total + bv
        sign = -1 if total < 0 else 1
        total = sign * (abs(total) % 1000000000)

        o_id = _edit(cu_id, 0, False, 'ZZZZ9')
        o_house = _edit(cu_house, 0, False, 'ZZZ9')
        o_bal = _edit(bal_digits, 2, bal_neg, '-----9.99')

        mm = _numval(cu_mm)
        if mm < 1 or mm > 12:
            flag = ' BADM'
        elif _numval(cu_opened) < 19000101:
            flag = ' OLD'
        else:
            flag = ''
        flag = flag.ljust(5)[:5]

        ws_out = (o_id + '|' + cu_first + ' ' + cu_last + '|' +
                  cu_city + ',' + o_house + ' ' + cu_road + '|' +
                  cu_dd + '/' + cu_mm + '/' + cu_yyyy + '|' +
                  o_bal + flag)
        out_file.append(ws_out.rstrip(' ') + '\n')

        if cu_last == ' ' * 10:
            name_copy = (cu_last + cu_first).ljust(20)
            out_stdout.append('NO LAST NAME ' + cu_id + ' [' + name_copy + ']\n')

    neg = total < 0
    tdig = str(abs(total)).rjust(9, '0')
    o_total = _edit(tdig, 2, neg, '-------9.99')
    out_stdout.append('COUNT ' + str(count).rjust(3, '0') + ' TOTAL ' + o_total + '\n')
    return (''.join(out_stdout).encode('latin-1'),
            {'CUSTLIST.DAT': ''.join(out_file).encode('latin-1')})

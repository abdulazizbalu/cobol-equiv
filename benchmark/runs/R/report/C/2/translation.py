def _expand(pic):
    out = []
    i = 0
    while i < len(pic):
        c = pic[i]
        if i + 1 < len(pic) and pic[i + 1] == '(':
            j = pic.index(')', i)
            n = int(pic[i + 2:j])
            out.append(c * n)
            i = j + 1
        else:
            out.append(c)
            i += 1
    return ''.join(out)


def _edit(pic, val, scale):
    pic = _expand(pic)
    tokens = []
    i = 0
    while i < len(pic):
        if pic[i:i + 2] in ('CR', 'DB'):
            tokens.append(pic[i:i + 2])
            i += 2
        else:
            tokens.append(pic[i])
            i += 1
    float_char = None
    if len(pic) > 1 and pic[0] in '$+-' and pic[1] == pic[0]:
        float_char = pic[0]
    # Determine float region (leading run of float chars, possibly with insertion chars)
    kinds = []  # 'digit', 'floatfirst', or None
    float_seen = False
    in_float = float_char is not None
    for idx, t in enumerate(tokens):
        if in_float:
            if t == float_char:
                if not float_seen:
                    kinds.append('floatfirst')
                    float_seen = True
                else:
                    kinds.append('digit')
                continue
            elif t in ',B/':
                kinds.append(None)
                continue
            else:
                in_float = False
        if t in ('9', 'Z', '*'):
            kinds.append('digit')
        else:
            kinds.append(None)
    int_d = 0
    dec_d = 0
    after_point = False
    for t, k in zip(tokens, kinds):
        if t == '.':
            after_point = True
        elif k == 'digit':
            if after_point:
                dec_d += 1
            else:
                int_d += 1
    absv = abs(val)
    if dec_d >= scale:
        n = absv * 10 ** (dec_d - scale)
    else:
        n = absv // 10 ** (scale - dec_d)
    total = int_d + dec_d
    n %= 10 ** total
    ds = str(n).zfill(total)
    is_zero = (n == 0)
    neg = val < 0 and not is_zero
    pad = '*' if '*' in pic else ' '
    out = []
    supp = True
    di = 0
    first_sig = None
    for t, k in zip(tokens, kinds):
        if k == 'digit':
            d = ds[di]
            di += 1
            if t == '9' or not supp or d != '0':
                if supp:
                    supp = False
                    first_sig = len(out)
                out.append(d)
            else:
                out.append('*' if t == '*' else ' ')
        elif k == 'floatfirst':
            out.append(' ')
        elif t in ',B/':
            if supp:
                out.append(pad)
            else:
                out.append(' ' if t == 'B' else t)
        elif t == '.':
            if supp:
                supp = False
                first_sig = len(out)
            out.append('.')
        elif t == 'CR':
            out.append('CR' if neg else '  ')
        elif t == 'DB':
            out.append('DB' if neg else '  ')
        elif t == '+':
            out.append('-' if neg else '+')
        elif t == '-':
            out.append('-' if neg else ' ')
        elif t == '$':
            out.append('$')
        else:
            out.append(t)
    if float_char and first_sig is not None and first_sig > 0:
        if float_char == '$':
            ch = '$'
        elif float_char == '+':
            ch = '-' if neg else '+'
        else:
            ch = '-' if neg else ' '
        out[first_sig - 1] = ch
    return ''.join(out)


def _digit(c):
    if '0' <= c <= '9':
        return ord(c) - 48
    if c == ' ':
        return 0
    return ord(c) & 0x0F


def _zoned(s):
    digits = 0
    for c in s[:-1]:
        digits = digits * 10 + _digit(c)
    last = s[-1]
    sign = 1
    if '0' <= last <= '9':
        d = ord(last) - 48
    elif 'p' <= last <= 'y':
        d = ord(last) - 0x70
        sign = -1
    elif last == '}':
        d = 0
        sign = -1
    elif 'J' <= last <= 'R':
        d = ord(last) - ord('J') + 1
        sign = -1
    elif last == '{':
        d = 0
    elif 'A' <= last <= 'I':
        d = ord(last) - ord('A') + 1
    else:
        d = _digit(last)
    return sign * (digits * 10 + d)


def _unsigned(s):
    v = 0
    for c in s:
        v = v * 10 + _digit(c)
    return v


def _trunc_add(a, b, digits):
    r = a + b
    m = 10 ** digits
    if r < 0:
        return -((-r) % m)
    return r % m


def main(stdin, input_files):
    data = input_files.get('AMOUNTS.DAT', b'').decode('latin-1')
    lines = data.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    out_lines = []
    ws_total = 0
    ws_qty = 0
    for line in lines:
        rec = (line + ' ' * 25)[:25]
        label = rec[0:6]
        value = _zoned(rec[6:15])
        date = _unsigned(rec[15:21])
        qty = _zoned(rec[21:25])
        l1 = (label + ' ' + _edit('ZZZ,ZZ9.99-', value, 2) + ' ' +
              _edit('$$$,$$$,$$9.99CR', value, 2) + ' ' +
              _edit('***,***,**9.99', value, 2) + ' ' +
              _edit('+ZZZ9', qty, 0) + ' ' +
              _edit('99/99/99', date, 0) + ' ' +
              _edit('---,--9', qty, 0))
        l2 = ('       ' + _edit('Z(4)9.999', value, 2) + ' ' +
              _edit('999B999', date, 0) + ' ' +
              _edit('$ZZ,ZZ9.99DB', value, 2) + ' ' +
              _edit('ZZ9.9+', value, 2) + ' ' +
              _edit('ZZZZ', qty, 0))
        out_lines.append(l1)
        out_lines.append(l2)
        ws_total = _trunc_add(ws_total, value, 11)
        ws_qty = _trunc_add(ws_qty, qty, 6)
    tl = ('TOTAL  ' + _edit('$$$$,$$$,$$9.99CR', ws_total, 2) +
          ' QTY ' + _edit('---,--9', ws_qty, 0))
    out_lines.append(tl)
    content = ''.join(l[:80].rstrip(' ') + '\n' for l in out_lines)
    return b'', {'REPORT.DAT': content.encode('latin-1')}

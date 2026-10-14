import re


def _expand(pic):
    return re.sub(r'(.)\((\d+)\)', lambda m: m.group(1) * int(m.group(2)), pic)


def _edit(pic, absval, scale, neg):
    pic = _expand(pic)
    suffix_kind = None
    if pic.endswith('CR') or pic.endswith('DB'):
        suffix_kind = pic[-2:]
        pic = pic[:-2]
    trailing_sign = None
    if pic and pic[-1] in '+-' and pic.count(pic[-1]) == 1:
        trailing_sign = pic[-1]
        pic = pic[:-1]
    leading = None
    float_ch = None
    if pic and pic[0] in '+-$':
        if pic.count(pic[0]) > 1:
            float_ch = pic[0]
        else:
            leading = pic[0]
            pic = pic[1:]

    # count digit positions
    n_int = 0
    n_frac = 0
    in_frac = False
    first_float = True
    for c in pic:
        if c == '.':
            in_frac = True
            continue
        is_digit = False
        if c in '9Z*':
            is_digit = True
        elif float_ch is not None and c == float_ch:
            if first_float:
                first_float = False
            else:
                is_digit = True
        if is_digit:
            if in_frac:
                n_frac += 1
            else:
                n_int += 1

    int_part = absval // (10 ** scale)
    frac_str = str(absval % (10 ** scale)).zfill(scale) if scale > 0 else ''
    if n_frac > len(frac_str):
        frac_str = frac_str + '0' * (n_frac - len(frac_str))
    else:
        frac_str = frac_str[:n_frac]
    int_str = str(int_part % (10 ** n_int)).zfill(n_int) if n_int > 0 else ''
    digits = int_str + frac_str
    is_zero = all(d == '0' for d in digits)
    neg_eff = neg and not is_zero

    pad = '*' if '*' in pic else ' '

    if '9' not in pic and is_zero:
        total_len = len(pic) + (1 if leading else 0) + (1 if trailing_sign else 0) + (2 if suffix_kind else 0)
        if pad == '*':
            body = ''.join('.' if c == '.' else '*' for c in pic)
            out = ('*' if leading else '') + body
            out += ('*' if trailing_sign else '') + ('**' if suffix_kind else '')
            return out
        return ' ' * total_len

    out = []
    significant = False
    sig_start = None
    di = 0
    first_float = True
    for c in pic:
        is_digit = False
        if c in '9Z*':
            is_digit = True
        elif float_ch is not None and c == float_ch:
            if first_float:
                first_float = False
                out.append(' ')
                continue
            is_digit = True
        if is_digit:
            d = digits[di]
            di += 1
            if c == '9':
                if not significant:
                    significant = True
                    sig_start = len(out)
                out.append(d)
            elif not significant and d == '0':
                out.append('*' if c == '*' else ' ')
            else:
                if not significant:
                    significant = True
                    sig_start = len(out)
                out.append(d)
        elif c == '.':
            if not significant:
                significant = True
                sig_start = len(out)
            out.append('.')
        elif c in ',B/':
            if significant:
                out.append(' ' if c == 'B' else c)
            else:
                out.append(pad)
        else:
            out.append(c)

    if float_ch is not None:
        if float_ch == '$':
            sym = '$'
        elif float_ch == '+':
            sym = '-' if neg_eff else '+'
        else:
            sym = '-' if neg_eff else ' '
        idx = (sig_start if sig_start is not None else len(out)) - 1
        if idx >= 0:
            out[idx] = sym

    body = ''.join(out)
    prefix = ''
    if leading == '$':
        prefix = '$'
    elif leading == '+':
        prefix = '-' if neg_eff else '+'
    elif leading == '-':
        prefix = '-' if neg_eff else ' '
    tail = ''
    if trailing_sign == '+':
        tail = '-' if neg_eff else '+'
    elif trailing_sign == '-':
        tail = '-' if neg_eff else ' '
    if suffix_kind:
        tail += suffix_kind if neg_eff else '  '
    return prefix + body + tail


def _digit(c):
    if '0' <= c <= '9':
        return ord(c) - 48
    return ord(c) & 0x0F if (ord(c) & 0x0F) <= 9 else 0


def _signed(field):
    body = field[:-1]
    last = field[-1]
    neg = False
    if '0' <= last <= '9':
        ld = ord(last) - 48
    elif 'p' <= last <= 'y':
        ld = ord(last) - ord('p')
        neg = True
    elif last == '{':
        ld = 0
    elif 'A' <= last <= 'I':
        ld = ord(last) - ord('A') + 1
    elif last == '}':
        ld = 0
        neg = True
    elif 'J' <= last <= 'R':
        ld = ord(last) - ord('J') + 1
        neg = True
    else:
        ld = _digit(last)
    v = 0
    for c in body:
        v = v * 10 + _digit(c)
    v = v * 10 + ld
    return v, neg


def main(stdin, input_files):
    data = input_files.get('AMOUNTS.DAT', b'').decode('latin-1')
    lines = data.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    out_lines = []
    total = 0
    qty_total = 0
    for line in lines:
        if line.endswith('\r'):
            line = line[:-1]
        rec = (line + ' ' * 25)[:25]
        label = rec[0:6]
        vabs, vneg = _signed(rec[6:15])
        date = 0
        for c in rec[15:21]:
            date = date * 10 + _digit(c)
        qabs, qneg = _signed(rec[21:25])

        l1 = (label + ' '
              + _edit('ZZZ,ZZ9.99-', vabs, 2, vneg) + ' '
              + _edit('$$$,$$$,$$9.99CR', vabs, 2, vneg) + ' '
              + _edit('***,***,**9.99', vabs, 2, vneg) + ' '
              + _edit('+ZZZ9', qabs, 0, qneg) + ' '
              + _edit('99/99/99', date, 0, False) + ' '
              + _edit('---,--9', qabs, 0, qneg))
        l2 = ('       '
              + _edit('Z(4)9.999', vabs, 2, vneg) + ' '
              + _edit('999B999', date, 0, False) + ' '
              + _edit('$ZZ,ZZ9.99DB', vabs, 2, vneg) + ' '
              + _edit('ZZ9.9+', vabs, 2, vneg) + ' '
              + _edit('ZZZZ', qabs, 0, qneg))
        out_lines.append(l1)
        out_lines.append(l2)

        total += -vabs if vneg else vabs
        s = -1 if total < 0 else 1
        total = s * (abs(total) % (10 ** 11))
        qty_total += -qabs if qneg else qabs
        s = -1 if qty_total < 0 else 1
        qty_total = s * (abs(qty_total) % (10 ** 6))

    tl = ('TOTAL  '
          + _edit('$$$$,$$$,$$9.99CR', abs(total), 2, total < 0)
          + ' QTY '
          + _edit('---,--9', abs(qty_total), 0, qty_total < 0))
    out_lines.append(tl)

    result = ''.join((l[:80]).rstrip(' ') + '\n' for l in out_lines)
    return b'', {'REPORT.DAT': result.encode('latin-1')}

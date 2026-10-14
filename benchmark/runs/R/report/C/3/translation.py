def _zoned(s, signed=True):
    """Decode a zoned decimal (trailing overpunch sign) string to an int."""
    if not s:
        return 0
    val = 0
    for c in s[:-1]:
        d = ord(c) & 0x0F
        if d > 9:
            d = 0
        val = val * 10 + d
    last = s[-1]
    neg = False
    if signed and 'p' <= last <= 'y':
        d = ord(last) - 0x70
        neg = True
    elif signed and last == '}':
        d = 0
        neg = True
    elif signed and 'J' <= last <= 'R':
        d = ord(last) - ord('J') + 1
        neg = True
    elif signed and last == '{':
        d = 0
    elif signed and 'A' <= last <= 'I':
        d = ord(last) - ord('A') + 1
    else:
        d = ord(last) & 0x0F
        if d > 9:
            d = 0
    val = val * 10 + d
    return -val if neg else val


def _edit(pic, val, scale):
    """Move a numeric value with the given scale into a numeric-edited picture."""
    float_ch = None
    for c in '$+-':
        if pic.count(c) > 1:
            float_ch = c
    check_protect = '*' in pic

    # Count integer and fraction digit positions.
    n_int = n_frac = 0
    seen_point = False
    first_float = True
    i = 0
    while i < len(pic):
        if pic[i:i + 2] in ('CR', 'DB'):
            i += 2
            continue
        c = pic[i]
        is_digit = False
        if c in '9Z*':
            is_digit = True
        elif float_ch is not None and c == float_ch:
            if first_float:
                first_float = False
            else:
                is_digit = True
        elif c == '.':
            seen_point = True
        if is_digit:
            if seen_point:
                n_frac += 1
            else:
                n_int += 1
        i += 1

    a = abs(val)
    if n_frac >= scale:
        a *= 10 ** (n_frac - scale)
    else:
        a //= 10 ** (scale - n_frac)
    a %= 10 ** (n_int + n_frac)
    D = str(a).zfill(n_int + n_frac)
    neg = val < 0 and a != 0

    if float_ch == '$':
        sym = '$'
    elif float_ch == '+':
        sym = '-' if neg else '+'
    elif float_ch == '-':
        sym = '-' if neg else ' '
    else:
        sym = None

    out = []
    di = 0
    sig = False
    first_float = True
    placed = False

    def become_sig():
        nonlocal sig, placed
        if not sig:
            sig = True
            if sym is not None and not placed:
                placed = True
                if out:
                    out[-1] = sym

    i = 0
    while i < len(pic):
        two = pic[i:i + 2]
        if two in ('CR', 'DB'):
            if neg:
                out.extend(two)
            else:
                out.extend('  ')
            i += 2
            continue
        c = pic[i]
        if c == '9':
            d = D[di]
            di += 1
            become_sig()
            out.append(d)
        elif c in 'Z*':
            d = D[di]
            di += 1
            if not sig and d == '0':
                out.append('*' if c == '*' else ' ')
            else:
                become_sig()
                out.append(d)
        elif float_ch is not None and c == float_ch:
            if first_float:
                first_float = False
                out.append(' ')
            else:
                d = D[di]
                di += 1
                if not sig and d == '0':
                    out.append(' ')
                else:
                    become_sig()
                    out.append(d)
        elif c in ',/':
            if sig:
                out.append(c)
            else:
                out.append('*' if check_protect else ' ')
        elif c == '.':
            out.append('.')
        elif c == 'B':
            out.append(' ')
        elif c == '0':
            out.append('0')
        elif c == '+':
            out.append('-' if neg else '+')
        elif c == '-':
            out.append('-' if neg else ' ')
        elif c == '$':
            out.append('$')
        else:
            out.append(c)
        i += 1
    return ''.join(out)


def main(stdin, input_files):
    data = input_files.get('AMOUNTS.DAT', b'').decode('latin-1')
    lines = data.split('\n')
    if lines and lines[-1] == '':
        lines.pop()

    out_lines = []
    total = 0
    qty_total = 0

    for line in lines:
        rec = line[:25].ljust(25, ' ')
        label = rec[0:6]
        value = _zoned(rec[6:15])
        date = _zoned(rec[15:21], signed=False)
        qty = _zoned(rec[21:25])

        l1 = (label + ' '
              + _edit('ZZZ,ZZ9.99-', value, 2) + ' '
              + _edit('$$$,$$$,$$9.99CR', value, 2) + ' '
              + _edit('***,***,**9.99', value, 2) + ' '
              + _edit('+ZZZ9', qty, 0) + ' '
              + _edit('99/99/99', date, 0) + ' '
              + _edit('---,--9', qty, 0))
        l2 = ('       '
              + _edit('ZZZZ9.999', value, 2) + ' '
              + _edit('999B999', date, 0) + ' '
              + _edit('$ZZ,ZZ9.99DB', value, 2) + ' '
              + _edit('ZZ9.9+', value, 2) + ' '
              + _edit('ZZZZ', abs(qty), 0))
        out_lines.append(l1[:80])
        out_lines.append(l2[:80])

        t = total + value
        s = -1 if t < 0 else 1
        total = s * (abs(t) % (10 ** 11))
        q = qty_total + qty
        s = -1 if q < 0 else 1
        qty_total = s * (abs(q) % (10 ** 6))

    tl = ('TOTAL  '
          + _edit('$$$$,$$$,$$9.99CR', total, 2)
          + ' QTY '
          + _edit('---,--9', qty_total, 0))
    out_lines.append(tl[:80])

    report = ''.join(l.rstrip(' ') + '\n' for l in out_lines)
    return b'', {'REPORT.DAT': report.encode('latin-1')}

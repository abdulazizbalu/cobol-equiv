def _digit(c):
    return c & 0x0F


def _decode_signed_trailing(b):
    """Decode a PIC S9(n) DISPLAY field with a trailing overpunched sign.
    Returns (value, negative_flag)."""
    neg = False
    val = 0
    n = len(b)
    for idx, c in enumerate(b):
        if idx == n - 1:
            ch = chr(c)
            if 'p' <= ch <= 'y':
                neg = True
                d = c - ord('p')
            elif ch == '}':
                neg = True
                d = 0
            elif 'J' <= ch <= 'R':
                neg = True
                d = c - ord('J') + 1
            elif ch == '{':
                d = 0
            elif 'A' <= ch <= 'I':
                d = c - ord('A') + 1
            else:
                d = _digit(c)
        else:
            d = _digit(c)
        val = val * 10 + d
    return val, neg


def _trunc(v, digits):
    m = 10 ** digits
    a = abs(v) % m
    return -a if v < 0 else a


def _edit(v):
    # PIC -(4)9
    a = abs(v) % 10000
    s = str(a)
    if v < 0 and a != 0:
        s = '-' + s
    return s.rjust(5)


def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get('CELLS.DAT', b'')
    lines = data.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()

    # cells: value and negative-zero flag
    cell = [[0] * 6 for _ in range(5)]
    negz = [[False] * 6 for _ in range(5)]
    bad = 0

    for line in lines:
        if line.endswith(b'\r'):
            line = line[:-1]
        rec = (line + b' ' * 6)[:6]
        row = _digit(rec[0])
        col = _digit(rec[1])
        op = rec[2:3]
        val, neg = _decode_signed_trailing(rec[3:6])
        sval = -val if neg else val
        if row < 1 or row > 4 or col < 1 or col > 5:
            bad = (bad + 1) % 100
        else:
            if op == b'=':
                cell[row][col] = _trunc(sval, 4)
                negz[row][col] = (neg and val == 0)
            elif op == b'+':
                cell[row][col] = _trunc(cell[row][col] + sval, 4)
                negz[row][col] = False
            elif op == b'*':
                cell[row][col] = _trunc(cell[row][col] * sval, 4)
                negz[row][col] = False
            else:
                bad = (bad + 1) % 100

    trans = [[0] * 5 for _ in range(6)]
    for i in range(1, 5):
        for j in range(1, 6):
            trans[j][i] = cell[i][j]

    mx = cell[1][1]
    mx_negz = negz[1][1]
    mi, mj = 1, 1
    out = []
    for i in range(1, 5):
        parts = []
        s = 0
        for j in range(1, 6):
            if cell[i][j] > mx:
                mx = cell[i][j]
                mx_negz = negz[i][j]
                mi, mj = i, j
            s += cell[i][j]
            parts.append(_edit(cell[i][j]) + ' ')
        s = _trunc(s, 5)
        ln = ''.join(parts)[:40].ljust(40)
        out.append(ln + '= ' + _edit(s))
    for j in range(1, 6):
        s = 0
        for i in range(1, 5):
            s += trans[j][i]
        s = _trunc(s, 5)
        out.append('COL ' + str(j) + ' ' + _edit(s))
    sign = '-' if (mx < 0 or (mx == 0 and mx_negz)) else '+'
    mxs = sign + str(abs(mx) % 10000).zfill(4)
    out.append('MAX ' + mxs + ' AT ' + str(mi) + ',' + str(mj) +
               ' BAD ' + str(bad).zfill(2))
    return ('\n'.join(out) + '\n').encode('latin-1'), {}

def _digit(b):
    if 48 <= b <= 57:
        return b - 48
    return b & 0x0F if (b & 0x0F) <= 9 else 0


def _parse_sval(bs):
    # PIC S9(3) with trailing overpunched sign
    digits = []
    neg = False
    for k, b in enumerate(bs):
        if k == len(bs) - 1:
            if 48 <= b <= 57:
                d = b - 48
            elif 0x70 <= b <= 0x79:
                d = b - 0x70
                neg = True
            elif b == ord('{'):
                d = 0
            elif ord('A') <= b <= ord('I'):
                d = b - ord('A') + 1
            elif b == ord('}'):
                d = 0
                neg = True
            elif ord('J') <= b <= ord('R'):
                d = b - ord('J') + 1
                neg = True
            else:
                d = _digit(b)
        else:
            d = _digit(b)
        digits.append(d)
    v = 0
    for d in digits:
        v = v * 10 + d
    return (-v if neg else v), (neg and v == 0)


def _trunc(v, n):
    m = 10 ** n
    a = abs(v) % m
    return -a if v < 0 else a


def _edit(v, negzero=False):
    a = abs(v) % 10000
    s = str(a)
    if v < 0 or negzero:
        s = "-" + s
    return s.rjust(5)


def main(stdin, input_files):
    data = input_files.get("CELLS.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    cells = [[0] * 5 for _ in range(4)]
    nz = [[False] * 5 for _ in range(4)]
    bad = 0

    for line in lines:
        if line.endswith(b"\r"):
            line = line[:-1]
        rec = (line[:6] + b" " * 6)[:6]
        row = _digit(rec[0])
        col = _digit(rec[1])
        op = rec[2:3]
        val, vnz = _parse_sval(rec[3:6])
        if row < 1 or row > 4 or col < 1 or col > 5:
            bad = (bad + 1) % 100
        else:
            r, c = row - 1, col - 1
            if op == b"=":
                cells[r][c] = _trunc(val, 4)
                nz[r][c] = vnz
            elif op == b"+":
                cells[r][c] = _trunc(cells[r][c] + val, 4)
                nz[r][c] = False
            elif op == b"*":
                cells[r][c] = _trunc(cells[r][c] * val, 4)
                nz[r][c] = False
            else:
                bad = (bad + 1) % 100

    out = []
    mx = cells[0][0]
    mxnz = nz[0][0]
    mi = mj = 1
    for i in range(4):
        line = ""
        s = 0
        for j in range(5):
            if cells[i][j] > mx:
                mx = cells[i][j]
                mxnz = nz[i][j]
                mi, mj = i + 1, j + 1
            s += cells[i][j]
            line += _edit(cells[i][j], nz[i][j]) + " "
        s = _trunc(s, 5)
        line = line[:40].ljust(40)
        out.append(line + "= " + _edit(s))
    for j in range(5):
        s = 0
        for i in range(4):
            s += cells[i][j]
        s = _trunc(s, 5)
        out.append("COL " + str(j + 1) + " " + _edit(s))
    sign = "-" if (mx < 0 or mxnz) else "+"
    out.append("MAX " + sign + "%04d" % abs(mx) + " AT " + str(mi) + "," + str(mj)
               + " BAD " + "%02d" % bad)
    return ("\n".join(out) + "\n").encode("latin-1"), {}

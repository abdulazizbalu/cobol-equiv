def _digit(c):
    return c & 0x0F if (0x30 <= c <= 0x39) else (c & 0x0F) % 10


def _decode_signed(b):
    # b: bytes of length 3, trailing overpunch sign
    neg = False
    digits = []
    for k, c in enumerate(b):
        if k == len(b) - 1:
            if 0x70 <= c <= 0x79:
                neg = True
                d = c - 0x70
            elif c == ord('}'):
                neg = True
                d = 0
            elif ord('J') <= c <= ord('R'):
                neg = True
                d = c - ord('J') + 1
            elif c == ord('{'):
                d = 0
            elif ord('A') <= c <= ord('I'):
                d = c - ord('A') + 1
            else:
                d = _digit(c)
        else:
            d = _digit(c)
        digits.append(d)
    v = 0
    for d in digits:
        v = v * 10 + d
    return -v if neg else v


def _trunc(v, n):
    m = 10 ** n
    a = abs(v) % m
    return -a if v < 0 else a


def _ed(v):
    a = abs(v) % 10000
    s = str(a)
    if v < 0 and a != 0:
        s = "-" + s
    return s.rjust(5)


def _signed4(v):
    return ("-" if v < 0 else "+") + str(abs(v)).zfill(4)


def main(stdin, input_files):
    data = input_files.get("CELLS.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    cells = [[0] * 5 for _ in range(4)]
    bad = 0
    for ln in lines:
        rec = ln[:6].ljust(6, b" ")
        row = _digit(rec[0])
        col = _digit(rec[1])
        op = rec[2:3]
        val = _decode_signed(rec[3:6])
        if row < 1 or row > 4 or col < 1 or col > 5:
            bad = (bad + 1) % 100
        else:
            r, c = row - 1, col - 1
            if op == b"=":
                cells[r][c] = _trunc(val, 4)
            elif op == b"+":
                cells[r][c] = _trunc(cells[r][c] + val, 4)
            elif op == b"*":
                cells[r][c] = _trunc(cells[r][c] * val, 4)
            else:
                bad = (bad + 1) % 100
    trans = [[cells[i][j] for i in range(4)] for j in range(5)]
    mx = cells[0][0]
    mi, mj = 1, 1
    out = []
    for i in range(4):
        line = ""
        s = 0
        for j in range(5):
            if cells[i][j] > mx:
                mx = cells[i][j]
                mi, mj = i + 1, j + 1
            s = _trunc(s + cells[i][j], 5)
            line += _ed(cells[i][j]) + " "
        line = line[:40].ljust(40)
        out.append(line + "= " + _ed(s))
    for j in range(5):
        s = 0
        for i in range(4):
            s = _trunc(s + trans[j][i], 5)
        out.append("COL " + str(j + 1) + " " + _ed(s))
    out.append("MAX " + _signed4(mx) + " AT " + str(mi) + "," + str(mj)
               + " BAD " + str(bad).zfill(2))
    return ("\n".join(out) + "\n").encode("latin-1"), {}

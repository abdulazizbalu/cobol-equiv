import sys


def _isspace(c):
    return c in (0x20, 0x09, 0x0A, 0x0B, 0x0C, 0x0D)


def _isdigit(c):
    return 0x30 <= c <= 0x39


def _move_alnum_to_display(src, int_digits, scale):
    """Emulate GnuCOBOL cob_move_alphanum_to_display; returns scaled int."""
    total = int_digits + scale
    dst = [ord('0')] * total
    s1 = 0
    e1 = len(src)
    s2 = 0
    e2 = total
    while s1 < e1 and _isspace(src[s1]):
        s1 += 1
    sign = 0
    if s1 != e1 and src[s1] in (ord('+'), ord('-')):
        sign = 1 if src[s1] == ord('+') else -1
        s1 += 1
    dec_pt = ord('.')
    num_sep = ord(',')
    count = 0
    p = s1
    while p < e1 and src[p] != dec_pt:
        if _isdigit(src[p]):
            count += 1
        p += 1
    size = int_digits
    if count < size:
        s2 += size - count
    else:
        while count > size:
            count -= 1
            while True:
                c = src[s1]
                s1 += 1
                if _isdigit(c):
                    break
    count = 0
    while s1 < e1 and s2 < e2:
        c = src[s1]
        if _isdigit(c):
            dst[s2] = c
            s2 += 1
        elif c == dec_pt:
            if count > 0:
                break
            count += 1
        elif not (_isspace(c) or c == num_sep):
            break
        s1 += 1
    val = int(bytes(dst).decode('ascii'))
    if sign < 0:
        val = -val
    return val


def _accept(lines, idx, field_size, int_digits, scale):
    if idx < len(lines):
        data = lines[idx]
    else:
        data = b' '
    if len(data) == 0:
        data = b' '
    data = data[:field_size]
    return _move_alnum_to_display(data, int_digits, scale)


def _split_lines(stdin):
    lines = []
    buf = stdin
    while buf:
        i = buf.find(b'\n')
        if i < 0:
            lines.append(buf)
            break
        lines.append(buf[:i])
        buf = buf[i + 1:]
    return lines


MOD = 10 ** 12


def _store(v):
    neg = v < 0
    m = abs(v) % MOD
    return -m if neg else m


def _tdiv(a, b):
    q = abs(a) // abs(b)
    if (a < 0) != (b < 0):
        q = -q
    return q


def main(stdin, input_files):
    lines = _split_lines(stdin)
    c_real = _accept(lines, 0, 4, 1, 3)
    c_imag = _accept(lines, 1, 4, 1, 3)
    out = []
    vertical = 1
    while not (vertical > 320):
        horizontal = 1
        row = []
        while not (horizontal > 560):
            x = _store((horizontal - 280) * 1000)
            y = _store((vertical - 160) * 1000)
            x = _store(_tdiv(x, 200))
            y = _store(_tdiv(y, 100))
            ch = '#'
            it = 1
            while not (it > 50 or ch == ' '):
                xs = _store(_tdiv(x * x, 1000))
                ys = _store(_tdiv(y * y, 1000))
                zr = _store(xs - ys)
                zr = _store(zr + c_real)
                xy = _store(_tdiv(x * y, 1000))
                zi = _store(xy * 2)
                zi = _store(zi + c_imag)
                zrs = _store(_tdiv(zr * zr, 1000))
                if zrs > 10000 * 1000:
                    ch = ' '
                x = zr
                y = zi
                it += 1
            row.append(ch)
            horizontal += 10
        out.append(''.join(row) + '\n')
        vertical += 10
    return ''.join(out).encode('latin-1'), {}


if __name__ == '__main__':
    data = sys.stdin.buffer.read()
    o, _ = main(data, {})
    sys.stdout.buffer.write(o)

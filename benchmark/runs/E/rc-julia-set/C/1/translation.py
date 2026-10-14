def _accept_numeric(line: bytes, size: int, scale: int) -> int:
    # Emulates GnuCOBOL ACCEPT into a signed numeric DISPLAY field.
    # Returns the value as an integer scaled by 10**scale.
    data = line[:size]
    n = len(data)
    i = 0
    ws = b" \t\n\v\f\r"
    while i < n and data[i] in ws:
        i += 1
    sign = 0
    if i < n and data[i] in (ord('+'), ord('-')):
        sign = 1 if data[i] == ord('+') else -1
        i += 1
    count = 0
    p = i
    while p < n and data[p] != ord('.'):
        if 48 <= data[p] <= 57:
            count += 1
        p += 1
    digits = ['0'] * size
    intsize = size - scale
    pos = 0
    if count < intsize:
        pos = intsize - count
    else:
        while count > intsize:
            count -= 1
            while True:
                c = data[i]
                i += 1
                if 48 <= c <= 57:
                    break
    dots = 0
    while i < n and pos < size:
        c = data[i]
        if 48 <= c <= 57:
            digits[pos] = chr(c)
            pos += 1
        elif c == ord('.'):
            if dots > 0:
                break
            dots += 1
        elif not (c in ws or c == ord(',')):
            break
        i += 1
    val = int(''.join(digits))
    if sign == -1:
        val = -val
    return val


_MOD = 10 ** 12  # S9(9)V999 -> 12 digits in thousandths


def _store(v: int) -> int:
    if v < 0:
        return -((-v) % _MOD)
    return v % _MOD


def _tdiv(a: int, b: int) -> int:
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) or q == 0 else -q


def _mul(a: int, b: int) -> int:
    # a, b in thousandths; result truncated to thousandths
    return _store(_tdiv(a * b, 1000))


def main(stdin: bytes, input_files: dict) -> tuple:
    lines = stdin.split(b"\n")
    l1 = lines[0] if len(lines) > 0 else b""
    l2 = lines[1] if len(lines) > 1 else b""
    c_real = _accept_numeric(l1, 4, 3)
    c_imag = _accept_numeric(l2, 4, 3)

    out = []
    vertical = 1
    while vertical <= 320:
        horizontal = 1
        row = []
        while horizontal <= 560:
            x = _store((horizontal - 280) * 1000)
            y = _store((vertical - 160) * 1000)
            x = _store(_tdiv(x, 200))
            y = _store(_tdiv(y, 100))
            ch = '#'
            it = 1
            while not (it > 50 or ch == ' '):
                xs = _mul(x, x)
                ys = _mul(y, y)
                zr = _store(xs - ys)
                zr = _store(zr + c_real)
                xy = _mul(x, y)
                zi = _store(xy * 2)
                zi = _store(zi + c_imag)
                zrs = _mul(zr, zr)
                if zrs > 10000 * 1000:
                    ch = ' '
                x = zr
                y = zi
                it += 1
            row.append(ch)
            horizontal += 10
        out.append(''.join(row) + " \n")
        vertical += 10
    return ''.join(out).encode('latin-1'), {}

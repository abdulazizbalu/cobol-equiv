def _isdigit(c):
    return 48 <= c <= 57


def _isspace(c):
    return c in (32, 9, 10, 11, 12, 13)


def _accept_num(line):
    # PIC S9V999 : field size 4, int digits 1, scale 3
    fsize = 4
    scale = 3
    data = line[:fsize]
    digits = [ord('0')] * fsize
    s1 = 0
    e1 = len(data)
    while s1 < e1 and _isspace(data[s1]):
        s1 += 1
    sign = 0
    if s1 != e1 and data[s1] in (ord('+'), ord('-')):
        sign = 1 if data[s1] == ord('+') else -1
        s1 += 1
    count = 0
    p = s1
    while p < e1 and data[p] != ord('.'):
        if _isdigit(data[p]):
            count += 1
        p += 1
    size = fsize - scale
    s2 = 0
    if count < size:
        s2 += size - count
    else:
        while count > size:
            count -= 1
            while True:
                if s1 >= e1:
                    break
                c = data[s1]
                s1 += 1
                if _isdigit(c):
                    break
    dots = 0
    while s1 < e1 and s2 < fsize:
        c = data[s1]
        if _isdigit(c):
            digits[s2] = c
            s2 += 1
        elif c == ord('.'):
            if dots > 0:
                break
            dots += 1
        elif not (_isspace(c) or c == ord(',')):
            break
        s1 += 1
    val = int(bytes(digits).decode())
    if sign < 0:
        val = -val
    return val  # in thousandths


_MOD = 10 ** 12


def _store(num, extra_scale):
    # num is in units of 10^-(3+extra_scale); truncate to thousandths and 12 digits
    if extra_scale > 0:
        d = 10 ** extra_scale
        q = abs(num) // d
    else:
        q = abs(num)
    q %= _MOD
    return -q if num < 0 else q


def main(stdin, input_files):
    lines = stdin.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    c_real = 0
    c_imag = 0
    if len(lines) > 0:
        l = lines[0]
        if l.endswith(b"\r"):
            l = l[:-1]
        c_real = _accept_num(l)
    if len(lines) > 1:
        l = lines[1]
        if l.endswith(b"\r"):
            l = l[:-1]
        c_imag = _accept_num(l)

    out = []
    vertical = 1
    while vertical <= 320:
        horizontal = 1
        while horizontal <= 560:
            x = _store((horizontal - 280) * 1000, 0)
            y = _store((vertical - 160) * 1000, 0)
            # DIVIDE X BY 200 GIVING X (truncate toward zero)
            ax = abs(x) // 200
            x = _store(-ax if x < 0 else ax, 0)
            ay = abs(y) // 100
            y = _store(-ay if y < 0 else ay, 0)
            ch = "#"
            it = 1
            while not (it > 50 or ch == " "):
                xsq = _store(x * x, 3)
                ysq = _store(y * y, 3)
                zr = _store(xsq - ysq, 0)
                zr = _store(zr + c_real, 0)
                xy = _store(x * y, 3)
                zi = _store(xy * 2, 0)
                zi = _store(zi + c_imag, 0)
                zrsq = _store(zr * zr, 3)
                if zrsq > 10000 * 1000:
                    ch = " "
                x = zr
                y = zi
                it += 1
            out.append(ch)
            horizontal += 10
        out.append(" \n")
        vertical += 10
    return "".join(out).encode(), {}

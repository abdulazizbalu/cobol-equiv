import sys

_FD = 360
_F = 10 ** _FD


def _tdiv(a, b):
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def _arctan_inv(n, one):
    x = one // n
    n2 = n * n
    total = x
    k = 1
    sign = -1
    while x:
        x //= n2
        term = x // (2 * k + 1)
        total += sign * term
        sign = -sign
        k += 1
    return total


def _compute_pi():
    one = 10 ** (_FD + 20)
    p = 4 * (4 * _arctan_inv(5, one) - _arctan_inv(239, one))
    return p // 10 ** 20


_PI_F = _compute_pi()
_TWO_PI_F = 2 * _PI_F


def _reduce(x):
    r = x % _TWO_PI_F
    if r > _PI_F:
        r -= _TWO_PI_F
    return r


def _sin_f(x):
    r = _reduce(x)
    r2 = r * r // _F
    term = r
    s = r
    k = 1
    while term:
        term = _tdiv(-term * r2, _F * (2 * k) * (2 * k + 1))
        s += term
        k += 1
    return s


def _cos_f(x):
    r = _reduce(x)
    r2 = r * r // _F
    term = _F
    s = _F
    k = 1
    while term:
        term = _tdiv(-term * r2, _F * (2 * k - 1) * (2 * k))
        s += term
        k += 1
    return s


def _atan_small(a):
    # 0 <= a <= F
    factor = 1
    for _ in range(4):
        a = a * _F // (_F + _isqrt(_F * _F + a * a))
        factor *= 2
    x2 = a * a // _F
    s = a
    p = a
    k = 1
    sign = -1
    while True:
        p = p * x2 // _F
        if p == 0:
            break
        t = p // (2 * k + 1)
        s += sign * t
        sign = -sign
        k += 1
    return s * factor


def _isqrt(n):
    import math
    return math.isqrt(n)


def _atan_f(x):
    if x == 0:
        return 0
    neg = x < 0
    a = abs(x)
    if a > _F:
        inv = _F * _F // a
        res = _PI_F // 2 - _atan_small(inv)
    else:
        res = _atan_small(a)
    return -res if neg else res


def _to_dec96(X):
    # fixed (scale _FD) -> decimal pair rounded to 96 significant digits
    if X == 0:
        return (0, 0)
    neg = X < 0
    a = abs(X)
    n = len(str(a))
    scale = _FD
    if n > 96:
        drop = n - 96
        d = 10 ** drop
        q, r = divmod(a, d)
        if 2 * r >= d:
            q += 1
        a = q
        scale = _FD - drop
    if scale < 0:
        a *= 10 ** (-scale)
        scale = 0
    return (-a if neg else a, scale)


def _to_fixed(p):
    v, s = p
    if s >= 0:
        return _tdiv(v * _F, 10 ** s)
    return v * 10 ** (-s) * _F


def _mul(a, b):
    return (a[0] * b[0], a[1] + b[1])


def _sub(a, b):
    v1, s1 = a
    v2, s2 = b
    if s1 < s2:
        v1 *= 10 ** (s2 - s1)
        s1 = s2
    elif s2 < s1:
        v2 *= 10 ** (s1 - s2)
    return (v1 - v2, s1)


def _div(a, b):
    v1, s1 = a
    v2, s2 = b
    if v2 == 0:
        return (0, 0)
    if v1 == 0:
        return (0, 0)
    s = s1 - s2
    shift = 38 + (-s if s < 0 else 0)
    v1 *= 10 ** shift
    s += shift
    return (_tdiv(v1, v2), s)


def _store(p, rounded=False):
    v, s = p
    neg = v < 0
    a = abs(v)
    if s > 5:
        d = 10 ** (s - 5)
        q, r = divmod(a, d)
        if rounded and 2 * r >= d:
            q += 1
        a = q
    elif s < 5:
        a *= 10 ** (5 - s)
    a %= 10 ** 8
    return -a if neg else a


def _fmt(v):
    neg = v < 0
    a = abs(v)
    ip = a // 100000
    fp = a % 100000
    s = str(ip)
    if neg:
        s = '-' + s
    return s.rjust(4) + '.' + ('%05d' % fp)


_SPACES = b' \t\n\v\f\r'


def _accept_num(line):
    s = line
    n = len(s)
    i = 0
    while i < n and s[i] in _SPACES:
        i += 1
    sign = 0
    if i < n and s[i] in b'+-':
        sign = 1 if s[i] == ord('+') else -1
        i += 1
    count = 0
    p = i
    while p < n and s[p] != ord('.'):
        if 48 <= s[p] <= 57:
            count += 1
        p += 1
    size = 31
    total = 36
    buf = ['0'] * total
    pos = 0
    if count < size:
        pos = size - count
    else:
        while count > size:
            count -= 1
            while i < n:
                c = s[i]
                i += 1
                if 48 <= c <= 57:
                    break
    dots = 0
    while i < n and pos < total:
        c = s[i]
        if 48 <= c <= 57:
            buf[pos] = chr(c)
            pos += 1
        elif c == ord('.'):
            if dots > 0:
                break
            dots += 1
        elif not (c in _SPACES or c == ord(',')):
            break
        i += 1
    val = int(''.join(buf)) % (10 ** 8)
    if sign < 0:
        val = -val
    return val


def main(stdin, input_files):
    lines = stdin.split(b'\n')
    if lines and lines[-1] == b'':
        lines = lines[:-1]
    idx = [0]

    def accept():
        if idx[0] < len(lines):
            l = lines[idx[0]]
            idx[0] += 1
            return _accept_num(l)
        return None

    out = []
    pi96 = _to_dec96(_PI_F)

    out.append("Enter latitude: ")
    latitude = 0
    r = accept()
    if r is not None:
        latitude = r
    out.append("Enter longitude: ")
    longitude = 0
    r = accept()
    if r is not None:
        longitude = r
    out.append("Enter legal meridian: ")
    legal = 0
    r = accept()
    if r is not None:
        legal = r
    out.append(" \n")

    # SIN(latitude * 2 * PI / 360)
    arg = _mul((latitude, 5), (2, 0))
    arg = _mul(arg, pi96)
    arg = _div(arg, (360, 0))
    sinres = _to_dec96(_sin_f(_to_fixed(arg)))
    lat_sine = _store(sinres, False)
    lat_sine_disp = _store(sinres, True)
    out.append("Sine of latitude: " + _fmt(lat_sine_disp).strip(' ') + "\n")

    diff = _sub((longitude, 5), (legal, 5))
    diff_longitude = _store(diff)
    diff_disp = _store(diff)
    out.append("Diff longitude: " + _fmt(diff_disp).strip(' ') + "\n")
    out.append(" \n")

    out.append("Time   Sun hour angle  Dial hour line angle\n")
    for hour in range(-6, 7):
        sha = _store(_sub((hour * 15, 0), (diff_longitude, 5)), True)
        a = _mul((sha, 5), (2, 0))
        a = _mul(a, pi96)
        a = _div(a, (360, 0))
        xf = _to_fixed(a)
        sf = _sin_f(xf)
        cf = _cos_f(xf)
        if cf == 0:
            tf = 0
        else:
            tf = _tdiv(sf * _F, cf)
        tanres = _to_dec96(tf)
        prod = _mul((lat_sine, 5), tanres)
        atanres = _to_dec96(_atan_f(_to_fixed(prod)))
        d = _mul(atanres, (360, 0))
        t = _mul((2, 0), pi96)
        d = _div(d, t)
        dial = _store(d, True)
        hd = (hour + 12) % 100
        out.append("%02d:00 " % hd + _fmt(sha) + "      " + _fmt(dial) + "\n")

    return ''.join(out).encode('latin-1'), {}

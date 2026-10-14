from decimal import Decimal, localcontext, ROUND_DOWN, ROUND_HALF_UP

PREC = 130
PI_C = Decimal('3.1415926535897932384626433832795029')
SCALE = 10 ** 5
MOD = 10 ** 8


def _compute_pi():
    with localcontext() as ctx:
        ctx.prec = PREC + 10
        three = Decimal(3)
        lasts, t, s, n, na, d, da = 0, three, 3, 1, 0, 0, 24
        while s != lasts:
            lasts = s
            n, na = n + na, na + 8
            d, da = d + da, da + 32
            t = (t * n) / d
            s += t
        return +s


TRUE_PI = None


def _sin(x):
    with localcontext() as ctx:
        ctx.prec = PREC
        two_pi = TRUE_PI * 2
        x = x - (x / two_pi).to_integral_value(rounding=ROUND_HALF_UP) * two_pi
        term = x
        s = x
        x2 = x * x
        n = 1
        while True:
            term = -term * x2 / ((n + 1) * (n + 2))
            n += 2
            ns = s + term
            if ns == s:
                break
            s = ns
        return s


def _cos(x):
    with localcontext() as ctx:
        ctx.prec = PREC
        two_pi = TRUE_PI * 2
        x = x - (x / two_pi).to_integral_value(rounding=ROUND_HALF_UP) * two_pi
        term = Decimal(1)
        s = Decimal(1)
        x2 = x * x
        n = 0
        while True:
            term = -term * x2 / ((n + 1) * (n + 2))
            n += 2
            ns = s + term
            if ns == s:
                break
            s = ns
        return s


def _atan(x):
    with localcontext() as ctx:
        ctx.prec = PREC
        if x == 0:
            return Decimal(0)
        neg = x < 0
        x = abs(x)
        inv = False
        if x > 1:
            x = 1 / x
            inv = True
        k = 0
        while x > Decimal('0.1'):
            x = x / (1 + (1 + x * x).sqrt())
            k += 1
        s = x
        term = x
        x2 = x * x
        n = 1
        while True:
            term = -term * x2
            n += 2
            add = term / n
            ns = s + add
            if ns == s:
                break
            s = ns
        s = s * (2 ** k)
        if inv:
            s = TRUE_PI / 2 - s
        if neg:
            s = -s
        return s


def _trunc(v):
    if v < 0:
        return -((-v) % MOD)
    return v % MOD


def _accept_num(line):
    # alphanumeric -> numeric display (8 digits, scale 5)
    data = line
    size_int = 3
    total = 8
    dst = ['0'] * total
    i = 0
    n = len(data)
    while i < n and chr(data[i]).isspace():
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
    pos = 0
    if count < size_int:
        pos = size_int - count
    else:
        while count > size_int:
            count -= 1
            while True:
                c = data[i]
                i += 1
                if 48 <= c <= 57:
                    break
    dots = 0
    while i < n and pos < total:
        c = data[i]
        if 48 <= c <= 57:
            dst[pos] = chr(c)
            pos += 1
        elif c == ord('.'):
            if dots > 0:
                break
            dots += 1
        elif not (chr(c).isspace() or c == ord(',')):
            break
        i += 1
    v = int(''.join(dst))
    if sign < 0:
        v = -v
    return v


def _edit(v):
    neg = v < 0
    a = abs(v)
    ip, fp = divmod(a, SCALE)
    s = str(ip)
    if neg:
        s = '-' + s
    return s.rjust(4) + '.' + '%05d' % fp


def main(stdin, input_files):
    global TRUE_PI
    if TRUE_PI is None:
        TRUE_PI = _compute_pi()
    lines = stdin.split(b'\n')
    if lines and lines[-1] == b'':
        lines = lines[:-1]
    li = [0]

    def accept(cur):
        if li[0] < len(lines):
            ln = lines[li[0]]
            li[0] += 1
            if ln.endswith(b'\r'):
                ln = ln[:-1]
            return _trunc(_accept_num(ln))
        return cur

    out = []
    out.append("Enter latitude: ")
    latitude = accept(0)
    out.append("Enter longitude: ")
    longitude = accept(0)
    out.append("Enter legal meridian: ")
    legal = accept(0)
    out.append(" \n")

    with localcontext() as ctx:
        ctx.prec = PREC
        x = Decimal(latitude) / SCALE * 2 * PI_C / 360
        s = _sin(x)
        lat_sine = _trunc(int((s * SCALE).to_integral_value(rounding=ROUND_DOWN)))
        lat_sine_disp = _trunc(int((s * SCALE).to_integral_value(rounding=ROUND_HALF_UP)))
    out.append("Sine of latitude: " + _edit(lat_sine_disp).lstrip(' ') + "\n")

    diff = _trunc(longitude - legal)
    out.append("Diff longitude: " + _edit(diff).lstrip(' ') + "\n")
    out.append(" \n")
    out.append("Time   Sun hour angle  Dial hour line angle\n")

    for hour in range(-6, 7):
        sha = _trunc(hour * 15 * SCALE - diff)
        with localcontext() as ctx:
            ctx.prec = PREC
            arg = Decimal(sha) / SCALE * 2 * PI_C / 360
            t = _sin(arg) / _cos(arg)
            p = Decimal(lat_sine) / SCALE * t
            a = _atan(p)
            r = a * 360 / (2 * PI_C)
            dial = _trunc(int((r * SCALE).to_integral_value(rounding=ROUND_HALF_UP)))
        hd = (hour + 12) % 100
        out.append("%02d" % hd + ":00 " + _edit(sha) + "      " + _edit(dial) + "\n")

    return ''.join(out).encode('latin-1'), {}

from decimal import Decimal, getcontext, ROUND_HALF_UP, ROUND_DOWN

getcontext().prec = 100

_PI_TRUE = Decimal(
    "3.14159265358979323846264338327950288419716939937510582097494459230781640628620899862803482534211706798214808651"
)
_PI_COB = Decimal("3.1415926535897932384626433832795029")

_SCALE = Decimal("0.00001")
_MOD = 10 ** 8


def _store(v, rounded):
    q = v.quantize(_SCALE, rounding=ROUND_HALF_UP if rounded else ROUND_DOWN)
    n = int(q.scaleb(5))
    neg = n < 0
    a = abs(n) % _MOD
    return -a if neg else a


def _to_dec(n):
    return Decimal(n).scaleb(-5)


def _sin(x):
    two_pi = 2 * _PI_TRUE
    x = x % two_pi
    if x > _PI_TRUE:
        x -= two_pi
    elif x < -_PI_TRUE:
        x += two_pi
    term = x
    s = x
    x2 = x * x
    k = 1
    eps = Decimal(10) ** -95
    while True:
        term = -term * x2 / ((2 * k) * (2 * k + 1))
        s += term
        k += 1
        if abs(term) < eps:
            break
    return s


def _cos(x):
    return _sin(x + _PI_TRUE / 2)


def _tan(x):
    return _sin(x) / _cos(x)


def _atan(x):
    if x == 0:
        return Decimal(0)
    if x < 0:
        return -_atan(-x)
    if x > 1:
        return _PI_TRUE / 2 - _atan(1 / x)
    halvings = 0
    while x > Decimal("0.1"):
        x = x / (1 + (1 + x * x).sqrt())
        halvings += 1
    term = x
    s = x
    x2 = x * x
    k = 1
    eps = Decimal(10) ** -95
    p = x
    while True:
        p = -p * x2
        term = p / (2 * k + 1)
        s += term
        k += 1
        if abs(term) < eps:
            break
    return s * (2 ** halvings)


def _parse_accept(line):
    s = line
    n = len(s)
    arr = ["0"] * 8
    i = 0
    spaces = " \t\n\v\f\r"
    while i < n and s[i] in spaces:
        i += 1
    sign = 1
    if i < n and s[i] in "+-":
        sign = 1 if s[i] == "+" else -1
        i += 1
    count = 0
    p = i
    while p < n and s[p] != ".":
        if s[p].isdigit():
            count += 1
        p += 1
    size = 3
    pos = 0
    if count < size:
        pos = size - count
    else:
        while count > size:
            count -= 1
            while i < n and not s[i].isdigit():
                i += 1
            i += 1
    cnt = 0
    while i < n and pos < 8:
        c = s[i]
        if c.isdigit():
            arr[pos] = c
            pos += 1
        elif c == ".":
            if cnt > 0:
                break
            cnt += 1
        elif not (c in spaces or c == ","):
            break
        i += 1
    v = int("".join(arr))
    return -v if sign < 0 else v


def _edit(n):
    neg = n < 0
    a = abs(n)
    ip = (a // 100000) % 1000
    fp = a % 100000
    s = ("-" if neg and a != 0 else "") + str(ip)
    return s.rjust(4) + "." + "%05d" % fp


def main(stdin, input_files):
    text = stdin.decode("latin-1")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    li = [0]

    def accept():
        if li[0] < len(lines):
            l = lines[li[0]]
            li[0] += 1
        else:
            l = ""
        if l.endswith("\r"):
            l = l[:-1]
        return _parse_accept(l)

    out = []
    out.append("Enter latitude: ")
    latitude = accept()
    out.append("Enter longitude: ")
    longitude = accept()
    out.append("Enter legal meridian: ")
    legal = accept()
    out.append(" \n")

    arg = _to_dec(latitude) * 2 * _PI_COB / 360
    sv = _sin(arg)
    lat_sine = _store(sv, False)
    lat_sine_disp = _store(sv, True)
    out.append("Sine of latitude: " + _edit(lat_sine_disp).strip(" ") + "\n")

    d = _to_dec(longitude) - _to_dec(legal)
    diff = _store(d, False)
    diff_disp = _store(d, False)
    out.append("Diff longitude: " + _edit(diff_disp).strip(" ") + "\n")
    out.append(" \n")

    out.append("Time   Sun hour angle  Dial hour line angle\n")
    ls = _to_dec(lat_sine)
    for hour in range(-6, 7):
        sha = _store(Decimal(hour * 15) - _to_dec(diff), True)
        t = _tan(_to_dec(sha) * 2 * _PI_COB / 360)
        val = _atan(ls * t) * 360 / (2 * _PI_COB)
        dial = _store(val, True)
        hd = (hour + 12) % 100
        out.append("%02d:00 " % hd + _edit(sha) + "      " + _edit(dial) + "\n")

    return "".join(out).encode("latin-1"), {}

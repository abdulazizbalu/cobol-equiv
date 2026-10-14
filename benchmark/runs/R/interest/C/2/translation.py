SCALE_SHIFT = 38


def _align(a, b):
    v1, s1 = a
    v2, s2 = b
    if s1 < s2:
        v1 *= 10 ** (s2 - s1)
        s1 = s2
    elif s2 < s1:
        v2 *= 10 ** (s1 - s2)
        s2 = s1
    return v1, v2, s1


def _add(a, b):
    v1, v2, s = _align(a, b)
    return (v1 + v2, s)


def _sub(a, b):
    v1, v2, s = _align(a, b)
    return (v1 - v2, s)


def _mul(a, b):
    return (a[0] * b[0], a[1] + b[1])


def _neg(a):
    return (-a[0], a[1])


def _tdiv(a, b):
    q = abs(a) // abs(b)
    if (a < 0) != (b < 0):
        q = -q
    return q


def _div(a, b):
    v1, s1 = a
    v2, s2 = b
    if v2 == 0:
        return None
    if v1 == 0:
        return (0, 0)
    scale = s1 - s2
    shift = SCALE_SHIFT + (-scale if scale < 0 else 0)
    v1 *= 10 ** shift
    scale += shift
    return (_tdiv(v1, v2), scale)


def _store(val, fscale, digits, rounded, signed=True):
    """Return (value_int_at_fscale, overflow, truncated_value)."""
    v, s = val
    if s > fscale:
        d = s - fscale
        a = abs(v)
        if rounded:
            a = (a + 5 * 10 ** (d - 1)) // 10 ** d
        else:
            a = a // 10 ** d
        v = -a if v < 0 else a
    elif s < fscale:
        v = v * 10 ** (fscale - s)
    if not signed:
        v = abs(v)
    overflow = abs(v) >= 10 ** digits
    a = abs(v) % (10 ** digits)
    trunc = -a if v < 0 else a
    return v, overflow, trunc


def _digit(c):
    return c & 0x0F


def _num(b):
    n = 0
    for c in b:
        n = n * 10 + _digit(c)
    return n


def _edit(value, scale, intwidth):
    a = abs(value)
    ip = a // 10 ** scale
    fp = a % 10 ** scale
    s = str(ip)
    if value < 0:
        s = "-" + s
    return s.rjust(intwidth) + "." + str(fp).zfill(scale)


def main(stdin, input_files):
    data = input_files.get("LOANS.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    out = []
    ws_compound = 0  # persists across records
    for line in lines:
        rec = line[:21].ljust(21, b" ")
        ln_id = rec[0:4]
        p = _num(rec[4:13])
        r = _num(rec[13:18])
        y = _num(rec[18:20])
        f = _num(rec[20:21])
        periods = {1: 1, 2: 2, 3: 4, 4: 12}.get(f, 0)
        if periods == 0 or y == 0 or y > 40:
            out.append(ln_id + b" INVALID\n")
            continue
        flag = "N"
        P = (p, 2)
        R = (r, 3)
        Y = (y, 0)
        N = (periods, 0)
        # simple
        t = _mul(_div(_mul(P, R), (100, 0)), Y)
        _, _, simple = _store(t, 2, 11, True)
        # period rate
        t = _div(_div(R, (100, 0)), N)
        _, _, prate = _store(t, 8, 9, False, signed=False)
        factor = 10 ** 8
        _, _, count = _store(_mul(N, Y), 0, 4, False, signed=False)
        for _ in range(count):
            t = _mul((factor, 8), _add((1, 0), (prate, 8)))
            v, ovf, _ = _store(t, 8, 11, True, signed=False)
            if ovf:
                flag = "Y"
            else:
                factor = v
        t = _sub(_mul(P, (factor, 8)), P)
        v, ovf, _ = _store(t, 2, 11, True)
        if ovf:
            flag = "Y"
        else:
            ws_compound = v
        # mixed
        a = _add(P, _mul(Y, (1000, 0)))
        b = _add(R, (1, 0))
        q = _div(a, b)
        m = _mul(_neg(Y), (25, 1))
        t = _sub(q, m)
        t = _sub(t, _div(N, (3, 0)))
        _, _, mixed = _store(t, 4, 11, False)
        # avg
        t = _div(_add((simple, 2), (ws_compound, 2)), (2, 0))
        _, _, avg = _store(t, 2, 11, True)
        s = (ln_id.decode("latin-1") + " S" + _edit(simple, 2, 10)
             + " C" + _edit(ws_compound, 2, 10)
             + " M" + _edit(mixed, 4, 8)
             + " F" + str(factor).zfill(11) + " " + flag + "\n")
        out.append(s.encode("latin-1"))
        s = ln_id.decode("latin-1") + " AVG" + _edit(avg, 2, 10) + "\n"
        out.append(s.encode("latin-1"))
    return b"".join(out), {}

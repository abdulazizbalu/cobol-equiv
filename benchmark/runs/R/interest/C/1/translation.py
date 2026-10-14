def _div(a, b):
    va, sa = a
    vb, sb = b
    if va == 0:
        return (0, 0)
    s = sa - sb
    shift = 38 + (-s if s < 0 else 0)
    va = va * (10 ** shift)
    s += shift
    neg = (va < 0) != (vb < 0)
    q = abs(va) // abs(vb)
    if neg:
        q = -q
    return (q, s)


def _mul(a, b):
    return (a[0] * b[0], a[1] + b[1])


def _align(a, b):
    va, sa = a
    vb, sb = b
    if sa < sb:
        va *= 10 ** (sb - sa)
        sa = sb
    elif sb < sa:
        vb *= 10 ** (sa - sb)
        sb = sa
    return va, vb, sa


def _add(a, b):
    va, vb, s = _align(a, b)
    return (va + vb, s)


def _sub(a, b):
    va, vb, s = _align(a, b)
    return (va - vb, s)


def _to_scale(a, t, rounded):
    v, s = a
    if s == t:
        return v
    if s < t:
        return v * 10 ** (t - s)
    d = 10 ** (s - t)
    neg = v < 0
    q, r = divmod(abs(v), d)
    if rounded and r * 2 >= d:
        q += 1
    return -q if neg else q


def _num(field):
    v = 0
    for ch in field:
        if 48 <= ch <= 57:
            v = v * 10 + (ch - 48)
        else:
            v = v * 10 + (ch & 0x0F if ch != 32 else 0) % 10
    return v


def _edit(v, scale, intwidth):
    neg = v < 0
    a = abs(v)
    ip = a // (10 ** scale)
    fp = a % (10 ** scale)
    s = ("-" if neg and a != 0 else "") + str(ip)
    return s.rjust(intwidth) + "." + str(fp).zfill(scale)


def main(stdin, input_files):
    data = input_files.get("LOANS.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    out = []
    compound = 0  # scale 2
    for line in lines:
        if line.endswith(b"\r"):
            line = line[:-1]
        rec = (line[:21]).ljust(21, b" ")
        ln_id = rec[0:4]
        P = (_num(rec[4:13]), 2)
        R = (_num(rec[13:18]), 3)
        Yv = _num(rec[18:20])
        Y = (Yv, 0)
        fq = _num(rec[20:21])
        periods = {1: 1, 2: 2, 3: 4, 4: 12}.get(fq, 0)
        if periods == 0 or Yv == 0 or Yv > 40:
            out.append(ln_id + b" INVALID\n")
            continue
        flag = "N"
        Pd = (periods, 0)
        simple = _to_scale(_mul(_div(_mul(P, R), (100, 0)), Y), 2, True)
        simple = (abs(simple) % 10 ** 11) * (1 if simple >= 0 else -1)
        pr = _to_scale(_div(_div(R, (100, 0)), Pd), 8, False)
        pr = abs(pr) % 10 ** 9
        factor = 10 ** 8
        count = (periods * Yv) % 10000
        for _ in range(count):
            r = _to_scale(_mul((factor, 8), _add((1, 0), (pr, 8))), 8, True)
            if abs(r) >= 10 ** 11:
                flag = "Y"
            else:
                factor = abs(r)
        r = _to_scale(_sub(_mul(P, (factor, 8)), P), 2, True)
        if abs(r) >= 10 ** 11:
            flag = "Y"
        else:
            compound = r
        a = _div(_add(P, _mul(Y, (1000, 0))), _add(R, (1, 0)))
        a = _sub(a, _mul((-Yv, 0), (25, 1)))
        a = _sub(a, _div(Pd, (3, 0)))
        m = _to_scale(a, 4, False)
        m = (abs(m) % 10 ** 11) * (1 if m >= 0 else -1)
        avg = _to_scale(_div(_add((simple, 2), (compound, 2)), (2, 0)), 2, True)
        avg = (abs(avg) % 10 ** 11) * (1 if avg >= 0 else -1)
        o1 = _edit(simple, 2, 10)
        o2 = _edit(compound, 2, 10)
        o3 = _edit(m, 4, 8)
        fs = str(factor).zfill(11)
        out.append(ln_id + (" S" + o1 + " C" + o2 + " M" + o3 + " F" + fs + " " + flag + "\n").encode())
        out.append(ln_id + (" AVG" + _edit(avg, 2, 10) + "\n").encode())
    return b"".join(out), {}

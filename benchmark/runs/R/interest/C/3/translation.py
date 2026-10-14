import sys

MAXD = 38


def _tdiv(a, b):
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


class D:
    __slots__ = ("v", "s")

    def __init__(self, v, s=0):
        self.v = v
        self.s = s

    def _align(self, o):
        a, b = self, o
        if a.s == b.s:
            return a.v, b.v, a.s
        if a.s < b.s:
            return a.v * 10 ** (b.s - a.s), b.v, b.s
        return a.v, b.v * 10 ** (a.s - b.s), a.s

    def __add__(self, o):
        x, y, s = self._align(o)
        return D(x + y, s)

    def __sub__(self, o):
        x, y, s = self._align(o)
        return D(x - y, s)

    def __mul__(self, o):
        return D(self.v * o.v, self.s + o.s)

    def __truediv__(self, o):
        if o.v == 0:
            raise ZeroDivisionError
        if self.v == 0:
            return D(0, 0)
        scale = self.s - o.s
        shift = MAXD + (-scale if scale < 0 else 0)
        v = self.v * 10 ** shift
        scale += shift
        return D(_tdiv(v, o.v), scale)


def store(d, digits, scale, rounded=False, keep=False, signed=True):
    """Return scaled integer, or None if size error with keep."""
    v = d.v
    if d.s > scale:
        diff = d.s - scale
        if rounded:
            if v >= 0:
                v += 5 * 10 ** (diff - 1)
            else:
                v -= 5 * 10 ** (diff - 1)
        v = _tdiv(v, 10 ** diff)
    elif d.s < scale:
        v = v * 10 ** (scale - d.s)
    if abs(v) >= 10 ** digits:
        if keep:
            return None
        v = (abs(v) % 10 ** digits) * (1 if v >= 0 else -1)
    if not signed:
        v = abs(v)
    return v


def num(bs):
    v = 0
    for b in bs:
        v = v * 10 + ((b & 0x0F) % 10)
    return v


def edit(v, scale, intwidth):
    neg = v < 0
    a = abs(v)
    ip = a // 10 ** scale
    fp = a % 10 ** scale
    s = str(ip)
    if neg and a != 0:
        s = "-" + s
    s = s.rjust(intwidth)[-intwidth:]
    return s + "." + str(fp).zfill(scale)


def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get("LOANS.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    out = []
    compound = 0  # S9(9)V99 scaled by 100, persists
    for line in lines:
        if line.endswith(b"\r"):
            line = line[:-1]
        rec = line[:21].ljust(21, b" ")
        ln_id = rec[0:4]
        P = D(num(rec[4:13]), 2)
        R = D(num(rec[13:18]), 3)
        yv = num(rec[18:20])
        Y = D(yv, 0)
        freq = num(rec[20:21])
        periods = {1: 1, 2: 2, 3: 4, 4: 12}.get(freq, 0)
        if periods == 0 or yv == 0 or yv > 40:
            out.append(ln_id + b" INVALID\n")
            continue
        flag = "N"
        PER = D(periods, 0)
        simple = store(P * R / D(100) * Y, 11, 2, rounded=True)
        prate = store(R / D(100) / PER, 9, 8, signed=False)
        factor = 100000000  # 1 at scale 8
        count = store(PER * Y, 4, 0, signed=False)
        for _ in range(count):
            r = store(D(factor, 8) * (D(1) + D(prate, 8)), 11, 8,
                      rounded=True, keep=True, signed=False)
            if r is None:
                flag = "Y"
            else:
                factor = r
        r = store(P * D(factor, 8) - P, 11, 2, rounded=True, keep=True)
        if r is None:
            flag = "Y"
        else:
            compound = r
        mixed_d = ((P + Y * D(1000)) / (R + D(1))
                   - (D(0) - Y) * D(25, 1) - PER / D(3))
        mixed = store(mixed_d, 11, 4)
        avg = store((D(simple, 2) + D(compound, 2)) / D(2), 11, 2, rounded=True)
        o1 = edit(simple, 2, 10)
        o2 = edit(compound, 2, 10)
        o3 = edit(mixed, 4, 8)
        fs = str(factor).zfill(11)
        out.append(ln_id + (" S" + o1 + " C" + o2 + " M" + o3 + " F" + fs
                            + " " + flag + "\n").encode("latin-1"))
        out.append(ln_id + (" AVG" + edit(avg, 2, 10) + "\n").encode("latin-1"))
    return b"".join(out), {}

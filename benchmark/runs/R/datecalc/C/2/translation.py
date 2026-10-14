def _digit_val(c):
    if '0' <= c <= '9':
        return ord(c) - 48
    return ord(c) & 0x0F if (ord(c) & 0x0F) <= 9 else 0


def _unsigned(s):
    v = 0
    for c in s:
        v = v * 10 + _digit_val(c)
    return v


def _signed(s):
    body = s[:-1]
    last = s[-1]
    neg = False
    if '0' <= last <= '9':
        d = ord(last) - 48
    elif last == '{':
        d = 0
    elif 'A' <= last <= 'I':
        d = ord(last) - ord('A') + 1
    elif last == '}':
        d = 0
        neg = True
    elif 'J' <= last <= 'R':
        d = ord(last) - ord('J') + 1
        neg = True
    elif 'p' <= last <= 'y':
        d = ord(last) - ord('p')
        neg = True
    else:
        d = _digit_val(last)
    v = _unsigned(body) * 10 + d
    return -v if neg else v


CUM = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
DIM = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
DOW = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


def _leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def _valid(yyyy, mm, dd):
    if yyyy < 1601 or mm < 1 or mm > 12 or dd < 1:
        return False
    maxday = DIM[mm - 1]
    if mm == 2 and _leap(yyyy):
        maxday += 1
    return dd <= maxday


def _to_num(yyyy, mm, dd):
    y = yyyy - 1601
    n = y * 365 + y // 4 - y // 100 + y // 400
    n += CUM[mm - 1] + dd - 1
    if _leap(yyyy) and mm > 2:
        n += 1
    return n


def _from_num(n):
    try_ = n
    yyyy = n // 366 + 1601
    mm = 1
    dd = 1
    while True:
        if yyyy == 9999:
            break
        yyyy += 1
        if _to_num(yyyy, mm, dd) > try_:
            yyyy -= 1
            break
    mm = 12
    dn = _to_num(yyyy, mm, dd)
    while not (dn <= try_):
        mm -= 1
        dn = _to_num(yyyy, mm, dd)
    dd = (try_ - dn + 1) % 100
    return "%04d%02d%02d" % (yyyy % 10000, mm, dd)


def main(stdin, input_files):
    data = input_files.get("DATES.DAT", b"").decode("latin-1")
    lines = data.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    out = []
    for line in lines:
        rec = line[:22].ljust(22)
        f_raw = rec[0:8]
        t_raw = rec[8:16]
        off = _signed(rec[16:22])
        fv = _unsigned(f_raw)
        fy, fm, fd = fv // 10000, (fv // 100) % 100, fv % 100
        if not _valid(fy, fm, fd):
            out.append(f_raw + " INVALID FROM DATE\n")
            continue
        fnum = _to_num(fy, fm, fd)
        tv = _unsigned(t_raw)
        ty, tm, td = tv // 10000, (tv // 100) % 100, tv % 100
        if not _valid(ty, tm, td):
            out.append(t_raw + " INVALID TO DATE\n")
            continue
        tnum = _to_num(ty, tm, td)
        diff = tnum - fnum
        s = str(abs(diff))
        if diff < 0:
            s = "-" + s
        diff_ed = s.rjust(8)[-8:]
        dow = DOW[fnum % 7]
        new = fnum + off
        if new < 0 or new > 3067670:
            res = "RANGE   "
        else:
            res = _from_num(new)
        out.append(f_raw + " " + t_raw + " " + diff_ed + " " + dow + " " + res + "\n")
    return "".join(out).encode("latin-1"), {}

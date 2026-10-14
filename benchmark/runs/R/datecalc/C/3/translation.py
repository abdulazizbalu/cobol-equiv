def _digits(s):
    v = 0
    for ch in s:
        v = v * 10 + ((ord(ch) & 0x0F) % 10 if not ch.isdigit() else int(ch))
    return v


def _signed_trailing(s):
    # PIC S9(n) DISPLAY with trailing embedded (overpunch) sign
    if not s:
        return 0
    body, last = s[:-1], s[-1]
    neg = False
    if last.isdigit():
        d = int(last)
    elif last == '{':
        d = 0
    elif 'A' <= last <= 'I':
        d = ord(last) - ord('A') + 1
    elif last == '}':
        d, neg = 0, True
    elif 'J' <= last <= 'R':
        d, neg = ord(last) - ord('J') + 1, True
    elif 'p' <= last <= 'y':
        d, neg = ord(last) - ord('p'), True
    else:
        d = (ord(last) & 0x0F) % 10
    v = _digits(body) * 10 + d
    return -v if neg else v


CUM = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
DIM = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
DOW = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


def _leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def _valid(y, m, d):
    if y < 1601 or m < 1 or m > 12 or d < 1:
        return False
    mx = DIM[m - 1]
    if m == 2 and _leap(y):
        mx += 1
    return d <= mx


def _to_num(y, m, d):
    yy = y - 1601
    n = yy * 365 + yy // 4 - yy // 100 + yy // 400
    n += CUM[m - 1] + d - 1
    if _leap(y) and m > 2:
        n += 1
    return n


def _from_num(n):
    try_ = n
    yyyy = n // 366 + 1601
    while True:
        if yyyy == 9999:
            break
        yyyy += 1
        if _to_num(yyyy, 1, 1) > try_:
            yyyy -= 1
            break
    mm = 12
    dn = _to_num(yyyy, mm, 1)
    while not (dn <= try_):
        mm -= 1
        dn = _to_num(yyyy, mm, 1)
    dd = try_ - dn + 1
    return "%04d%02d%02d" % (yyyy % 10000, mm % 100, dd % 100)


def main(stdin, input_files):
    data = input_files.get("DATES.DAT", b"").decode("latin-1")
    lines = data.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    out = []
    for line in lines:
        if line.endswith("\r"):
            line = line[:-1]
        rec = (line + " " * 22)[:22]
        f_raw, t_raw, o_raw = rec[0:8], rec[8:16], rec[16:22]
        fv = _digits(f_raw)
        y, m, d = fv // 10000, (fv // 100) % 100, fv % 100
        if not _valid(y, m, d):
            out.append(f_raw + " INVALID FROM DATE")
            continue
        fnum = _to_num(y, m, d)
        tv = _digits(t_raw)
        y2, m2, d2 = tv // 10000, (tv // 100) % 100, tv % 100
        if not _valid(y2, m2, d2):
            out.append(t_raw + " INVALID TO DATE")
            continue
        tnum = _to_num(y2, m2, d2)
        diff = tnum - fnum
        diff_ed = str(diff).rjust(8)
        dow = DOW[fnum % 7]
        off = _signed_trailing(o_raw)
        new = fnum + off
        if new < 0 or new > 3067670:
            res = "RANGE   "
        else:
            res = _from_num(new)
        out.append(f_raw + " " + t_raw + " " + diff_ed + " " + dow + " " + res)
    s = "".join(l + "\n" for l in out)
    return s.encode("latin-1"), {}

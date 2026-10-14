def _digits_val(s):
    v = 0
    for c in s:
        if '0' <= c <= '9':
            d = ord(c) - 48
        else:
            d = (ord(c) & 0x0F) % 10
        v = v * 10 + d
    return v


def _signed_val(s):
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
        d = (ord(last) & 0x0F) % 10
    v = _digits_val(body) * 10 + d
    return -v if neg else v


CUM = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
DIM = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
DOW = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


def _leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def _valid(yyyy, mm, dd):
    if yyyy < 1601 or mm < 1 or mm > 12 or dd < 1:
        return False
    mx = DIM[mm - 1]
    if mm == 2 and _leap(yyyy):
        mx += 1
    return dd <= mx


def _to_num(yyyy, mm, dd):
    y = (yyyy - 1601) % 100000
    n = y * 365 + y // 4 - y // 100 + y // 400
    n += CUM[mm - 1] + dd - 1
    if _leap(yyyy) and mm > 2:
        n += 1
    return n


def _num_to_date(num):
    tr = num
    yyyy = num // 366 + 1601
    while True:
        if yyyy == 9999:
            break
        yyyy += 1
        if _to_num(yyyy, 1, 1) > tr:
            yyyy -= 1
            break
    mm = 12
    dn = _to_num(yyyy, mm, 1)
    while dn > tr:
        mm -= 1
        dn = _to_num(yyyy, mm, 1)
    dd = (tr - dn + 1) % 100
    return "%04d%02d%02d" % (yyyy % 10000, mm, dd)


def _edit(v):
    s = str(abs(v))
    if v < 0:
        s = "-" + s
    return s.rjust(8)[-8:]


def main(stdin, input_files):
    data = input_files.get("DATES.DAT", b"").decode("latin-1")
    lines = data.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    out = []
    for line in lines:
        if line.endswith("\r"):
            line = line[:-1]
        rec = line[:22].ljust(22)
        f_s = rec[0:8]
        t_s = rec[8:16]
        o_s = rec[16:22]
        fv = _digits_val(f_s)
        y, m, d = fv // 10000, (fv // 100) % 100, fv % 100
        if not _valid(y, m, d):
            out.append(f_s + " INVALID FROM DATE")
            continue
        fnum = _to_num(y, m, d)
        tv = _digits_val(t_s)
        y2, m2, d2 = tv // 10000, (tv // 100) % 100, tv % 100
        if not _valid(y2, m2, d2):
            out.append(t_s + " INVALID TO DATE")
            continue
        tnum = _to_num(y2, m2, d2)
        diff = tnum - fnum
        ed = _edit(diff)
        dix = fnum % 7
        off = _signed_val(o_s)
        new = fnum + off
        if new < 0 or new > 3067670:
            res = "RANGE   "
        else:
            res = _num_to_date(new)
        out.append(f_s + " " + t_s + " " + ed + " " + DOW[dix] + " " + res)
    text = "".join(l + "\n" for l in out)
    return text.encode("latin-1"), {}

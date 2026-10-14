def _digit(c):
    return c & 0x0F


def _decode_amount(b):
    # PIC S9(5)V99, trailing overpunched sign
    v = 0
    for c in b[:6]:
        v = v * 10 + _digit(c)
    last = b[6]
    neg = False
    if 0x30 <= last <= 0x39:
        d = last - 0x30
    elif 0x70 <= last <= 0x79:
        d = last - 0x70
        neg = True
    elif last == ord('{'):
        d = 0
    elif ord('A') <= last <= ord('I'):
        d = last - ord('A') + 1
    elif last == ord('}'):
        d = 0
        neg = True
    elif ord('J') <= last <= ord('R'):
        d = last - ord('J') + 1
        neg = True
    else:
        d = _digit(last)
    v = v * 10 + d
    return -v if neg else v


def _trunc_signed(v, digits):
    m = 10 ** digits
    a = abs(v) % m
    return -a if v < 0 else a


def _edit(cents):
    # PIC -(6)9.99 ; cents is signed integer in hundredths
    neg = cents < 0
    a = abs(cents) % (10 ** 8)
    ip = a // 100
    fp = a % 100
    s = str(ip)
    if neg:
        s = "-" + s
    return s.rjust(7) + "." + "%02d" % fp


class _Sum:
    def __init__(self):
        self.region = b"  "
        self.name = bytearray(b" " * 10)
        self.amt = [0] * 13
        self.cnt = [0] * 13
        self.total = 0
        self.best = 0


def main(stdin, input_files):
    data = input_files.get("SALES.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    out = []
    rs = _Sum()
    first = True
    rejects = 0

    def print_region():
        best = 1
        for m in range(1, 13):
            if rs.cnt[m] > 0:
                out.append(rs.region + b" " + ("%02d" % m).encode() + b" "
                           + _edit(rs.amt[m]).encode() + b" "
                           + ("%03d" % rs.cnt[m]).encode())
            if rs.amt[m] > rs.amt[best]:
                best = m
        rs.best = best
        shown = _edit(rs.total)
        out.append(bytes(rs.name) + b" TOTAL " + shown.encode()
                   + b" BEST " + ("%02d" % best).encode())

    for line in lines:
        rec = line[:11]
        if len(rec) < 11:
            rec = rec + b" " * (11 - len(rec))
        region = rec[0:2]
        month = _digit(rec[2]) * 10 + _digit(rec[3])
        amount = _decode_amount(rec[4:11])
        if month < 1 or month > 12:
            rejects = (rejects + 1) % 1000
        else:
            if not first and region != rs.region:
                print_region()
                rs = _Sum()
            first = False
            rs.region = region
            src = b"REGION " + region
            rs.name[0:len(src)] = src
            rs.amt[month] = _trunc_signed(rs.amt[month] + amount, 8)
            rs.total = _trunc_signed(rs.total + amount, 9)
            rs.cnt[month] = (rs.cnt[month] + 1) % 1000

    if not first:
        print_region()
    out.append(b"REJECTED " + ("%03d" % rejects).encode())
    return b"".join(l + b"\n" for l in out), {}

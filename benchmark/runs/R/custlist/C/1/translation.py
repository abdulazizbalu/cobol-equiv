def _digit(c):
    # numeric value of a display digit byte (low nibble, as GnuCOBOL does for valid data)
    if 0x30 <= c <= 0x39:
        return c - 0x30
    if c == 0x20:
        return 0
    return c & 0x0F


def _unsigned(b):
    v = 0
    for c in b:
        v = v * 10 + _digit(c)
    return v


def _signed_trailing(b):
    # PIC S9(n) DISPLAY with trailing embedded sign
    head = b[:-1]
    last = b[-1]
    neg = False
    if 0x30 <= last <= 0x39:
        d = last - 0x30
    elif last == 0x20:
        d = 0
    elif 0x70 <= last <= 0x79:
        neg = True
        d = last - 0x70
    elif last == ord('{'):
        d = 0
    elif ord('A') <= last <= ord('I'):
        d = last - ord('A') + 1
    elif last == ord('}'):
        neg = True
        d = 0
    elif ord('J') <= last <= ord('R'):
        neg = True
        d = last - ord('J') + 1
    else:
        neg = True
        d = last & 0x0F
        if d > 9:
            d = 0
    v = _unsigned(head) * 10 + d
    return -v if neg else v


def _float_minus(value_cents, int_digits):
    # picture -(k)9.99 where int positions = int_digits + 1 (one for sign)
    neg = value_cents < 0
    a = abs(value_cents)
    ip = a // 100
    fp = a % 100
    ip %= 10 ** int_digits
    s = str(ip)
    if neg and (ip != 0 or fp != 0):
        s = "-" + s
    return s.rjust(int_digits + 1) + "." + "%02d" % fp


def main(stdin, input_files):
    data = input_files.get("CUST.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    out = bytearray()
    lst = bytearray()
    count = 0
    total = 0  # cents, S9(7)V99

    for line in lines:
        rec = line[:64].ljust(64, b" ")
        cu_id = rec[0:5]
        cu_last = rec[5:15]
        cu_first = rec[15:23]
        cu_house = rec[23:27]
        cu_road = rec[27:39]
        cu_city = rec[39:49]
        cu_yyyy = rec[49:53]
        cu_mm = rec[53:55]
        cu_dd = rec[55:57]
        cu_opened = rec[49:57]
        cu_bal = rec[57:64]

        count = (count + 1) % 1000
        bal = _signed_trailing(cu_bal)
        t = total + bal
        neg = t < 0
        t = abs(t) % (10 ** 9)
        total = -t if neg else t

        mm = _unsigned(cu_mm)
        opened = _unsigned(cu_opened)
        if mm < 1 or mm > 12:
            flag = b" BADM"
        elif opened < 19000101:
            flag = b" OLD "
        else:
            flag = b"     "

        o = bytearray()
        o += str(_unsigned(cu_id) % 100000).rjust(5).encode()
        o += b"|"
        o += cu_first + b" " + cu_last
        o += b"|"
        o += cu_city + b","
        o += str(_unsigned(cu_house) % 10000).rjust(4).encode()
        o += b" " + cu_road
        o += b"|"
        o += bytes(cu_dd) + b"/" + bytes(cu_mm) + b"/" + bytes(cu_yyyy)
        o += b"|"
        o += _float_minus(bal, 5).encode()
        o += flag
        lst += bytes(o).rstrip(b" ") + b"\n"

        if cu_last == b" " * 10:
            name = (cu_last + cu_first).ljust(20, b" ")
            out += b"NO LAST NAME " + cu_id + b" [" + name + b"]\n"

    out += b"COUNT " + ("%03d" % count).encode() + b" TOTAL " + _float_minus(total, 7).encode() + b"\n"
    return bytes(out), {"CUSTLIST.DAT": bytes(lst)}

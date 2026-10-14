def _digit(b):
    return b & 0x0F


def _parse_unsigned(bs):
    v = 0
    for b in bs:
        v = v * 10 + _digit(b)
    return v


def _parse_signed_trailing(bs):
    # PIC S9(n) DISPLAY with trailing overpunched sign
    v = 0
    for b in bs[:-1]:
        v = v * 10 + _digit(b)
    last = bs[-1]
    neg = False
    if 0x30 <= last <= 0x39:
        d = last - 0x30
    elif last == 0x20:
        d = 0
    elif 0x70 <= last <= 0x79:      # 'p'..'y'
        d = last - 0x70
        neg = True
    elif last == 0x7D:              # '}'
        d = 0
        neg = True
    elif 0x4A <= last <= 0x52:      # 'J'..'R'
        d = last - 0x49
        neg = True
    elif last == 0x7B:              # '{'
        d = 0
    elif 0x41 <= last <= 0x49:      # 'A'..'I'
        d = last - 0x40
    else:
        d = last & 0x0F
    v = v * 10 + d
    return -v if neg else v


def _trunc(v, digits):
    m = 10 ** digits
    if v < 0:
        return -((-v) % m)
    return v % m


def _edit(v):
    # PIC -(6)9.99, v in hundredths
    neg = v < 0
    a = abs(v)
    ip = (a // 100) % 1000000
    fp = a % 100
    s = str(ip)
    if neg:
        s = "-" + s
    return s.rjust(7) + "." + "%02d" % fp


def main(stdin, input_files):
    data = input_files.get("SALES.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    out = []
    state = {}

    def init():
        state["region"] = b"  "
        state["name"] = bytearray(b" " * 10)
        state["amt"] = [0] * 13
        state["cnt"] = [0] * 13
        state["total"] = 0

    def print_region():
        best = 1
        amt = state["amt"]
        cnt = state["cnt"]
        for m in range(1, 13):
            if cnt[m] > 0:
                out.append(state["region"] + b" " + b"%02d" % m + b" " +
                           _edit(amt[m]).encode("latin-1") + b" " +
                           b"%03d" % cnt[m] + b"\n")
            if amt[m] > amt[best]:
                best = m
        out.append(bytes(state["name"]) + b" TOTAL " +
                   _edit(state["total"]).encode("latin-1") +
                   b" BEST " + b"%02d" % best + b"\n")

    init()
    first = True
    rejects = 0

    for line in lines:
        rec = line[:11].ljust(11, b" ")
        region = rec[0:2]
        month = _parse_unsigned(rec[2:4])
        amount = _parse_signed_trailing(rec[4:11])
        if month < 1 or month > 12:
            rejects = (rejects + 1) % 1000
        else:
            if not first and region != state["region"]:
                print_region()
                init()
            first = False
            state["region"] = region
            src = b"REGION " + region
            name = state["name"]
            for i, b in enumerate(src[:10]):
                name[i] = b
            state["amt"][month] = _trunc(state["amt"][month] + amount, 8)
            state["total"] = _trunc(state["total"] + amount, 9)
            state["cnt"][month] = (state["cnt"][month] + 1) % 1000

    if not first:
        print_region()
    out.append(b"REJECTED " + b"%03d" % rejects + b"\n")
    return b"".join(out), {}

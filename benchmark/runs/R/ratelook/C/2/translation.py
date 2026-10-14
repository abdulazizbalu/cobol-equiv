from fractions import Fraction

_RATE_DATA = [
    "AAE0450001250",
    "AAS0300000800",
    "BKE0600001575",
    "BKS0420001010",
    "CNE0725002030",
    "CNS0510001333",
    "DEE0999002500",
    "DES0650001725",
    "FRE0880002200",
    "FRS0600001480",
    "UZE1200003125",
    "UZS0875002250",
]


def _num(s):
    v = 0
    for ch in s:
        v = v * 10 + (ord(ch) & 0x0F) % 10
    return v


def _digits(s):
    return "".join(str((ord(ch) & 0x0F) % 10) for ch in s)


def _split_records(data):
    text = data.decode("latin-1")
    if text == "":
        return []
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    recs = []
    for ln in lines:
        if ln.endswith("\r"):
            ln = ln[:-1]
        ln = ln[:9].ljust(9)
        recs.append(ln)
    return recs


def _edit(cents, width):
    ip = cents // 100
    fp = cents % 100
    return ("{:,}".format(ip) + "." + "%02d" % fp).rjust(width)


def main(stdin, input_files):
    table = []
    for e in _RATE_DATA:
        table.append((e[0:2], e[2:3], _num(e[3:8]), _num(e[8:13])))

    out = []
    found = 0
    missing = 0
    total = 0  # cents

    data = input_files.get("SHIPS.DAT", b"")
    for rec in _split_records(data):
        zone = rec[0:2]
        cls = rec[2:3]
        wraw = rec[3:7]
        qraw = rec[7:9]
        entry = None
        # binary search over sorted table
        lo, hi = 0, len(table) - 1
        key = zone + cls
        while lo <= hi:
            mid = (lo + hi) // 2
            k = table[mid][0] + table[mid][1]
            if k == key:
                entry = table[mid]
                break
            elif k < key:
                lo = mid + 1
            else:
                hi = mid - 1
        if entry is None:
            missing = (missing + 1) % 1000
            out.append("NO RATE " + zone + "/" + cls)
        else:
            found = (found + 1) % 1000
            base = Fraction(entry[2], 100)
            perkg = Fraction(entry[3], 100)
            w = Fraction(_num(wraw), 10)
            q = _num(qraw)
            charge = (base + perkg * w) * q * (100 - Fraction(q, 4)) / 100
            c = charge * 100
            if c >= 0:
                cents = int((c + Fraction(1, 2)).__floor__())
            else:
                cents = -int((-c + Fraction(1, 2)).__floor__())
            cents = abs(cents) % (10 ** 9)
            total = (total + cents) % (10 ** 10)
            wd = _digits(wraw)
            out.append(zone + cls + " " + _digits(qraw) + " x " +
                       wd[0:3] + "." + wd[3] + " = " + _edit(cents, 12))

    out.append("PRICED %03d MISSING %03d TOTAL %s" %
               (found, missing, _edit(total, 13)))
    stdout = ("\n".join(out) + "\n").encode("latin-1")
    return stdout, {}

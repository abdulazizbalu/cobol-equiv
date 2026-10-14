from fractions import Fraction


def _digit(c):
    return ord(c) & 0x0F


def _num(s):
    v = 0
    for c in s:
        v = v * 10 + _digit(c)
    return v


def _edit(value_cents, int_digits):
    # value_cents: non-negative integer, 2 decimal places
    ip = value_cents // 100
    fp = value_cents % 100
    istr = str(ip).rjust(int_digits, "0")[-int_digits:]
    out = []
    started = False
    for i, ch in enumerate(istr):
        pos_from_right = int_digits - i  # digits remaining including this one
        if i == int_digits - 1:
            started = True
        if ch != "0":
            started = True
        out.append(ch if started else " ")
        rem = pos_from_right - 1
        if rem > 0 and rem % 3 == 0:
            out.append("," if started else " ")
    return "".join(out) + "." + "%02d" % fp


RATE_DATA = [
    "AAE0450001250", "AAS0300000800", "BKE0600001575", "BKS0420001010",
    "CNE0725002030", "CNS0510001333", "DEE0999002500", "DES0650001725",
    "FRE0880002200", "FRS0600001480", "UZE1200003125", "UZS0875002250",
]


def _search_all(zone, cls):
    lo, hi = 0, len(RATE_DATA) - 1
    key = zone + cls
    while lo <= hi:
        mid = (lo + hi) // 2
        k = RATE_DATA[mid][:3]
        if k == key:
            return mid
        if k < key:
            lo = mid + 1
        else:
            hi = mid - 1
    return None


def main(stdin, input_files):
    data = input_files.get("SHIPS.DAT", b"").decode("latin-1")
    lines = data.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    out = []
    total = 0  # cents
    found = 0
    missing = 0
    for line in lines:
        rec = line[:9].ljust(9)
        zone = rec[0:2]
        cls = rec[2]
        wstr = rec[3:7]
        qstr = rec[7:9]
        idx = _search_all(zone, cls)
        if idx is None:
            missing = (missing + 1) % 1000
            out.append("NO RATE " + zone + "/" + cls)
        else:
            found = (found + 1) % 1000
            e = RATE_DATA[idx]
            base = Fraction(_num(e[3:8]), 100)
            perkg = Fraction(_num(e[8:13]), 100)
            weight = Fraction(_num(wstr), 10)
            qty = Fraction(_num(qstr))
            val = (base + perkg * weight) * qty * (100 - qty / 4) / 100
            scaled = val * 100
            if scaled >= 0:
                cents = int(scaled + Fraction(1, 2))
            else:
                cents = -int(-scaled + Fraction(1, 2))
            cents = abs(cents) % (10 ** 9)
            total = (total + cents) % (10 ** 10)
            out.append(zone + cls + " " + qstr + " x " + wstr[:3] + "." + wstr[3]
                       + " = " + _edit(cents, 7))
    out.append("PRICED %03d MISSING %03d TOTAL %s" % (found, missing, _edit(total, 8)))
    text = "".join(l + "\n" for l in out)
    return text.encode("latin-1"), {}

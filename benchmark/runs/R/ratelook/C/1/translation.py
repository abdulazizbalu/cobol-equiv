from fractions import Fraction

RATE_DATA = [
    "AAE0450001250", "AAS0300000800", "BKE0600001575", "BKS0420001010",
    "CNE0725002030", "CNS0510001333", "DEE0999002500", "DES0650001725",
    "FRE0880002200", "FRS0600001480", "UZE1200003125", "UZS0875002250",
]

RATES = {}
for _e in RATE_DATA:
    RATES[_e[0:3]] = (int(_e[3:8]), int(_e[8:13]))  # in hundredths


def _num(b):
    v = 0
    for c in b:
        v = v * 10 + ((c - 48) % 10 if 48 <= c <= 57 else (c & 0x0F) % 10)
    return v


def _edit(cents, width):
    s = "{:,.2f}".format(cents / 100) if cents < 10 ** 15 else None
    ip, fp = divmod(cents, 100)
    s = "{:,}".format(ip) + "." + "%02d" % fp
    return s.rjust(width)[-width:]


def _round_half_up(fr):
    # fr is non-negative Fraction; return integer rounded half away from zero
    n, d = fr.numerator, fr.denominator
    if n < 0:
        q = (-n * 2 + d) // (2 * d)
        return -q
    return (n * 2 + d) // (2 * d)


def main(stdin, input_files):
    data = input_files.get("SHIPS.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    out = []
    found = 0
    missing = 0
    total = 0  # cents
    for line in lines:
        rec = line[:9].ljust(9, b" ")
        zone = rec[0:2]
        cls = rec[2:3]
        wraw = rec[3:7]
        qraw = rec[7:9]
        key = (zone + cls).decode("latin-1")
        if key not in RATES:
            missing = (missing + 1) % 1000
            out.append(b"NO RATE " + zone + b"/" + cls + b"\n")
            continue
        found = (found + 1) % 1000
        base, perkg = RATES[key]
        weight = _num(wraw)  # tenths
        qty = _num(qraw)
        val = (Fraction(base, 100) + Fraction(perkg, 100) * Fraction(weight, 10)) \
            * qty * (100 - Fraction(qty, 4)) / 100
        charge = _round_half_up(val * 100) % (10 ** 9)
        total = (total + charge) % (10 ** 10)
        wdisp = wraw[0:3] + b"." + wraw[3:4]
        out.append(zone + cls + b" " + qraw + b" x " + wdisp + b" = "
                   + _edit(charge, 12).encode("latin-1") + b"\n")
    out.append(("PRICED %03d MISSING %03d TOTAL " % (found, missing)).encode("latin-1")
               + _edit(total, 13).encode("latin-1") + b"\n")
    return b"".join(out), {}

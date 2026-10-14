def _edit(pic, int_digits, dec_digits, value):
    """Generic numeric editing for the pictures used by the program."""
    neg = value < 0
    mag = abs(value)
    s = str(mag).rjust(int_digits + dec_digits, "0")
    s = s[-(int_digits + dec_digits):]
    ipart = s[:int_digits]
    dpart = s[int_digits:]
    floatc = None
    if pic.count("$") > 1:
        floatc = "$"
    elif pic.startswith("-"):
        floatc = "-"
    out = []
    started = False
    first_float_seen = False
    di = 0
    in_dec = False
    dj = 0
    i = 0
    n = len(pic)
    while i < n:
        c = pic[i]
        if in_dec:
            if c == "9":
                out.append(dpart[dj])
                dj += 1
            elif c == "C" and i + 1 < n and pic[i + 1] == "R":
                out.append("CR" if neg else "  ")
                i += 1
            elif c == "-":
                out.append("-" if neg else " ")
            else:
                out.append(c)
            i += 1
            continue
        if c == ".":
            in_dec = True
            out.append(".")
        elif c == ",":
            out.append("," if started else " ")
        elif floatc is not None and c == floatc and not first_float_seen:
            first_float_seen = True
            out.append(" ")
        elif c in "Z9" or (floatc is not None and c == floatc):
            d = ipart[di]
            di += 1
            if not started and d == "0" and c != "9":
                out.append(" ")
            else:
                if not started:
                    started = True
                    if floatc is not None:
                        sym = "$" if floatc == "$" else ("-" if neg else " ")
                        out[-1] = sym
                out.append(d)
        else:
            out.append(c)
        i += 1
    return "".join(out)


def _decode_amount(b):
    val = 0
    for c in b[:-1]:
        val = val * 10 + (c & 0x0F)
    c = b[-1]
    neg = False
    if 0x70 <= c <= 0x79:
        d = c - 0x70
        neg = True
    elif c == ord("}"):
        d = 0
        neg = True
    elif ord("J") <= c <= ord("R"):
        d = c - ord("J") + 1
        neg = True
    elif c == ord("{"):
        d = 0
    elif ord("A") <= c <= ord("I"):
        d = c - ord("A") + 1
    else:
        d = c & 0x0F
    val = val * 10 + d
    return -val if neg else val


def _trunc(v, digits):
    m = 10 ** digits
    if v < 0:
        return -((-v) % m)
    return v % m


def main(stdin, input_files):
    data = input_files.get("SALES.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    records = []
    for ln in lines:
        r = ln[:12]
        r = r + b" " * (12 - len(r))
        records.append(r)

    out = []

    def write(s):
        s = s[:40].ljust(40)
        out.append(s.rstrip(" ") + "\n")

    st = {
        "first": True, "prev_region": b"  ", "prev_branch": b"   ",
        "btot": 0, "bcnt": 0, "rtot": 0, "gtot": 0, "gcnt": 0,
        "sl_region": b"  ", "sl_branch": b"   ",
    }

    def branch_break():
        line = ("    " + st["prev_region"].decode("latin-1") + "/" +
                st["prev_branch"].decode("latin-1") + " " +
                _edit("ZZZ9", 4, 0, st["bcnt"]) + " " +
                _edit("Z,ZZZ,ZZ9.99CR", 7, 2, st["btot"]))
        write(line)
        st["rtot"] = _trunc(st["rtot"] + st["btot"], 10)
        st["btot"] = 0
        st["bcnt"] = 0
        st["prev_branch"] = st["sl_branch"]

    def region_break():
        line = ("REGION " + st["prev_region"].decode("latin-1") + " TOTAL" +
                _edit("---,---,--9.99", 8, 2, st["rtot"]))
        write(line)
        st["gtot"] = _trunc(st["gtot"] + st["rtot"], 11)
        st["rtot"] = 0
        st["prev_region"] = st["sl_region"]

    for r in records:
        st["sl_region"] = r[0:2]
        st["sl_branch"] = r[2:5]
        amt = _decode_amount(r[5:12])
        if st["first"]:
            st["first"] = False
            st["prev_region"] = st["sl_region"]
            st["prev_branch"] = st["sl_branch"]
            st["btot"] = 0
            st["bcnt"] = 0
            st["rtot"] = 0
        else:
            if st["sl_region"] != st["prev_region"]:
                branch_break()
                region_break()
            elif st["sl_branch"] != st["prev_branch"]:
                branch_break()
        st["btot"] = _trunc(st["btot"] + amt, 9)
        st["bcnt"] = (st["bcnt"] + 1) % 10000
        st["gcnt"] = (st["gcnt"] + 1) % 100000

    if st["first"]:
        write("NO DATA")
    else:
        branch_break()
        region_break()
    line = ("GRAND " + _edit("ZZ,ZZ9", 5, 0, st["gcnt"]) + " " +
            _edit("$$$$,$$$,$$9.99-", 9, 2, st["gtot"]))
    write(line)
    return b"", {"REPORT.DAT": "".join(out).encode("latin-1")}

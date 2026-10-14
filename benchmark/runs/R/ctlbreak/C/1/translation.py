def _edit_int(digits, pat, float_sym=None):
    f = pat[0] if pat[0] in "$-" else None
    digit_pos = []
    for i, ch in enumerate(pat):
        if ch in "Z9":
            digit_pos.append(i)
        elif f is not None and ch == f and i != 0:
            digit_pos.append(i)
    assert len(digit_pos) == len(digits)
    out = list(pat)
    dmap = {}
    for p, d in zip(digit_pos, digits):
        dmap[p] = d
    sig = len(pat)
    for p in digit_pos:
        if dmap[p] != "0" or pat[p] == "9":
            sig = p
            break
    res = []
    for i in range(len(pat)):
        if i < sig:
            res.append(" ")
        else:
            if i in dmap:
                res.append(dmap[i])
            else:
                res.append(out[i])
    if f is not None and sig - 1 >= 0:
        res[sig - 1] = float_sym if float_sym is not None else f
    return "".join(res)


def _split(v, intdigits):
    neg = v < 0
    a = abs(v)
    s = str(a).rjust(intdigits + 2, "0")[-(intdigits + 2):]
    return neg, s[:intdigits], s[intdigits:]


def _trunc(v, mod):
    if v < 0:
        return -((-v) % mod)
    return v % mod


def _fmt_branch_total(v):
    neg, i, fr = _split(v, 7)
    return _edit_int(i, "Z,ZZZ,ZZ9") + "." + fr + ("CR" if neg else "  ")


def _fmt_region_total(v):
    neg, i, fr = _split(v, 8)
    return _edit_int(i, "---,---,--9", "-" if neg else " ") + "." + fr


def _fmt_grand_total(v):
    neg, i, fr = _split(v, 9)
    return _edit_int(i, "$$$$,$$$,$$9") + "." + fr + ("-" if neg else " ")


def _parse_amount(b):
    n = 0
    for c in b[:6]:
        n = n * 10 + (c & 0x0F)
    c = b[6]
    neg = False
    if 0x70 <= c <= 0x79:
        neg = True
        d = c - 0x70
    else:
        d = c & 0x0F
    n = n * 10 + d
    return -n if neg else n


def main(stdin, input_files):
    data = input_files.get("SALES.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    out = []

    def write(s):
        s = s[:40].rstrip(" ")
        out.append(s + "\n")

    first = True
    prev_region = "  "
    prev_branch = "   "
    branch_tot = 0
    branch_cnt = 0
    region_tot = 0
    grand_tot = 0
    grand_cnt = 0
    sl_region = "  "
    sl_branch = "   "

    def branch_break():
        nonlocal branch_tot, branch_cnt, region_tot, prev_branch
        line = ("    " + prev_region + "/" + prev_branch + " "
                + _edit_int(str(branch_cnt).rjust(4, "0")[-4:], "ZZZ9")
                + " " + _fmt_branch_total(branch_tot))
        write(line)
        region_tot = _trunc(region_tot + branch_tot, 10 ** 10)
        branch_tot = 0
        branch_cnt = 0
        prev_branch = sl_branch

    def region_break():
        nonlocal region_tot, grand_tot, prev_region
        line = "REGION " + prev_region + " TOTAL" + _fmt_region_total(region_tot)
        write(line)
        grand_tot = _trunc(grand_tot + region_tot, 10 ** 11)
        region_tot = 0
        prev_region = sl_region

    for raw in lines:
        rec = raw[:12].ljust(12, b" ")
        sl_region = rec[0:2].decode("latin-1")
        sl_branch = rec[2:5].decode("latin-1")
        amt = _parse_amount(rec[5:12])
        if first:
            first = False
            prev_region = sl_region
            prev_branch = sl_branch
            branch_tot = 0
            branch_cnt = 0
            region_tot = 0
        else:
            if sl_region != prev_region:
                branch_break()
                region_break()
            elif sl_branch != prev_branch:
                branch_break()
        branch_tot = _trunc(branch_tot + amt, 10 ** 9)
        branch_cnt = (branch_cnt + 1) % 10000
        grand_cnt = (grand_cnt + 1) % 100000

    if first:
        write("NO DATA")
    else:
        branch_break()
        region_break()
    gl = ("GRAND " + _edit_int(str(grand_cnt).rjust(5, "0"), "ZZ,ZZ9")
          + " " + _fmt_grand_total(grand_tot))
    write(gl)
    return b"", {"REPORT.DAT": "".join(out).encode("latin-1")}

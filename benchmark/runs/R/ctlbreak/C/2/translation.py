def _amount(field: str) -> int:
    """Decode PIC S9(5)V99 DISPLAY (trailing overpunch sign) into cents."""
    digits = []
    neg = False
    for i, ch in enumerate(field):
        o = ord(ch)
        if i == len(field) - 1:
            if 'p' <= ch <= 'y':
                neg = True
                digits.append(o - ord('p'))
                continue
            if ch == '}':
                neg = True
                digits.append(0)
                continue
            if 'J' <= ch <= 'R':
                neg = True
                digits.append(o - ord('J') + 1)
                continue
            if ch == '{':
                digits.append(0)
                continue
            if 'A' <= ch <= 'I':
                digits.append(o - ord('A') + 1)
                continue
        if '0' <= ch <= '9':
            digits.append(o - 48)
        else:
            digits.append((o & 0x0F) % 10)
    v = 0
    for d in digits:
        v = v * 10 + d
    return -v if neg else v


def _trunc(v: int, ndigits: int) -> int:
    m = 10 ** ndigits
    if v < 0:
        return -((-v) % m)
    return v % m


def _edit_int(pat: str, n: int, float_char=None, symbol=' ') -> str:
    dpos = []
    seen_float = False
    for i, c in enumerate(pat):
        if c in 'Z9':
            dpos.append(i)
        elif float_char is not None and c == float_char:
            if seen_float:
                dpos.append(i)
            else:
                seen_float = True
    s = str(n).zfill(len(dpos))[-len(dpos):]
    out = list(pat)
    sig = None
    for k, i in enumerate(dpos):
        out[i] = s[k]
        if sig is None and (s[k] != '0' or pat[i] == '9'):
            sig = i
    if sig is None:
        sig = len(pat)
    for i in range(sig):
        out[i] = ' '
    if float_char is not None and sig - 1 >= 0:
        out[sig - 1] = symbol
    return ''.join(out)


def _bl_total(cents: int) -> str:
    neg = cents < 0
    a = abs(cents)
    ip, fp = divmod(a, 100)
    s = _edit_int("Z,ZZZ,ZZ9", ip) + "." + "%02d" % fp
    return s + ("CR" if neg else "  ")


def _rl_total(cents: int) -> str:
    neg = cents < 0
    a = abs(cents)
    ip, fp = divmod(a, 100)
    return _edit_int("---,---,--9", ip, '-', '-' if neg else ' ') + "." + "%02d" % fp


def _gl_total(cents: int) -> str:
    neg = cents < 0
    a = abs(cents)
    ip, fp = divmod(a, 100)
    return _edit_int("$$$$,$$$,$$9", ip, '$', '$') + "." + "%02d" % fp + ("-" if neg else " ")


def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get('SALES.DAT', b'')
    lines = data.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
    out_lines = []

    def write(s: str):
        s = s[:40].ljust(40)
        out_lines.append(s.rstrip(' '))

    first = True
    prev_region = '  '
    prev_branch = '   '
    branch_tot = 0
    branch_cnt = 0
    region_tot = 0
    grand_tot = 0
    grand_cnt = 0
    sl_region = '  '
    sl_branch = '   '

    def branch_break():
        nonlocal branch_tot, branch_cnt, region_tot, prev_branch
        line = ("    " + prev_region + "/" + prev_branch + " "
                + _edit_int("ZZZ9", branch_cnt) + " " + _bl_total(branch_tot))
        write(line)
        region_tot = _trunc(region_tot + branch_tot, 10)
        branch_tot = 0
        branch_cnt = 0
        prev_branch = sl_branch

    def region_break():
        nonlocal region_tot, grand_tot, prev_region
        line = "REGION " + prev_region + " TOTAL" + _rl_total(region_tot)
        write(line)
        grand_tot = _trunc(grand_tot + region_tot, 11)
        region_tot = 0
        prev_region = sl_region

    for raw in lines:
        rec = raw.decode('latin-1')
        rec = rec[:12].ljust(12)
        sl_region = rec[0:2]
        sl_branch = rec[2:5]
        amt = _amount(rec[5:12])
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
        branch_tot = _trunc(branch_tot + amt, 9)
        branch_cnt = (branch_cnt + 1) % 10000
        grand_cnt = (grand_cnt + 1) % 100000

    if first:
        write("NO DATA")
    else:
        branch_break()
        region_break()

    line = "GRAND " + _edit_int("ZZ,ZZ9", grand_cnt) + " " + _gl_total(grand_tot)
    write(line)

    content = ''.join(l + '\n' for l in out_lines).encode('latin-1')
    return b'', {'REPORT.DAT': content}

import datetime

_BASE = datetime.date(1601, 1, 1).toordinal() - 1


def _alnum_to_num(s: bytes, size: int) -> int:
    # Emulates GnuCOBOL MOVE alphanumeric -> unsigned numeric DISPLAY
    out = [ord('0')] * size
    i = 0
    n = len(s)
    while i < n and chr(s[i]).isspace():
        i += 1
    if i < n and s[i] in (ord('+'), ord('-')):
        i += 1
    count = 0
    p = i
    while p < n and s[p] != ord('.'):
        if 48 <= s[p] <= 57:
            count += 1
        p += 1
    pos = 0
    if count < size:
        pos = size - count
    else:
        while count > size:
            count -= 1
            while i < n:
                c = s[i]
                i += 1
                if 48 <= c <= 57:
                    break
    dots = 0
    while i < n and pos < size:
        c = s[i]
        if 48 <= c <= 57:
            out[pos] = c
            pos += 1
        elif c == ord('.'):
            if dots > 0:
                break
            dots += 1
        elif not (chr(c).isspace() or c == ord(',')):
            break
        i += 1
    return int(bytes(out).decode())


def main(stdin: bytes, input_files: dict) -> tuple:
    out = []
    out.append(b"Enter a calendar year (1601 thru 9999): ")
    lines = stdin.split(b"\n")
    if stdin == b"":
        line = b""
    else:
        line = lines[0]
        if line.endswith(b"\r"):
            line = line[:-1]
    yr = _alnum_to_num(line, 4)
    if not (1601 <= yr <= 9999):
        out.append(b"Invalid year\n")
        return b"".join(out), {}
    mo = 1
    da = 1
    for _ in range(12):
        da = 1
        mo += 1
        if mo > 12:
            mo = 12
            da = 31
        int_date = datetime.date(yr, mo, da).toordinal() - _BASE
        if not (mo == 12 and da == 31):
            int_date -= 1
        d = datetime.date.fromordinal(int_date + _BASE)
        yr, mo, da = d.year, d.month, d.day
        dow = ((int_date - 1) % 7) + 1
        dow = (dow - 5) % 7
        da -= dow
        out.append(b"%04d-%02d-%02d\n" % (yr, mo, da))
        mo += 1
    return b"".join(out), {}

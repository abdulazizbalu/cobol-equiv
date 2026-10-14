import datetime


def _alnum_to_display(src: bytes, size: int) -> str:
    out = ['0'] * size
    s = 0
    e = len(src)
    while s < e and chr(src[s]).isspace():
        s += 1
    if s < e and src[s] in (ord('+'), ord('-')):
        s += 1
    count = 0
    p = s
    while p < e and src[p] != ord('.'):
        if chr(src[p]).isdigit():
            count += 1
        p += 1
    pos = 0
    if count < size:
        pos = size - count
    else:
        while count > size:
            count -= 1
            while s < e:
                c = src[s]
                s += 1
                if chr(c).isdigit():
                    break
    dots = 0
    while s < e and pos < size:
        c = chr(src[s])
        if c.isdigit():
            out[pos] = c
            pos += 1
        elif c == '.':
            if dots > 0:
                break
            dots += 1
        elif not (c.isspace() or c == ','):
            break
        s += 1
    return ''.join(out)


def main(stdin: bytes, input_files: dict) -> tuple:
    out = []
    out.append("Enter a calendar year (1601 thru 9999): ")
    yr = 0
    if stdin:
        line = stdin.split(b'\n', 1)[0]
        if line.endswith(b'\r'):
            line = line[:-1]
        yr = int(_alnum_to_display(line, 4))
    if not (1601 <= yr <= 9999):
        out.append("Invalid year\n")
        return ''.join(out).encode('latin-1'), {}
    for m in range(1, 13):
        if m == 12:
            d = datetime.date(yr, 12, 31)
        else:
            d = datetime.date(yr, m + 1, 1) - datetime.timedelta(days=1)
        dow = d.weekday() + 1
        dow = (dow - 5) % 7
        da = d.day - dow
        out.append("%04d-%02d-%02d\n" % (yr, d.month, da))
    return ''.join(out).encode('latin-1'), {}

def _move_alnum_to_num(src: bytes, size: int) -> str:
    out = ['0'] * size
    s = 0
    e = len(src)
    while s < e and chr(src[s]).isspace():
        s += 1
    if s < e and src[s:s + 1] in (b'+', b'-'):
        s += 1
    count = 0
    p = s
    while p < e and src[p:p + 1] != b'.':
        if 48 <= src[p] <= 57:
            count += 1
        p += 1
    pos = 0
    if count < size:
        pos = size - count
    else:
        while count > size:
            while True:
                c = src[s]
                s += 1
                if 48 <= c <= 57:
                    break
            count -= 1
    dots = 0
    while s < e and pos < size:
        c = src[s]
        if 48 <= c <= 57:
            out[pos] = chr(c)
            pos += 1
        elif c == ord('.'):
            if dots > 0:
                break
            dots += 1
        elif not (chr(c).isspace() or c == ord(',')):
            break
        s += 1
    return ''.join(out)


def _is_leap(y: int) -> bool:
    return (y % 4 == 0 and y % 100 != 0) or y % 400 == 0


def main(stdin: bytes, input_files: dict) -> tuple:
    out = []
    out.append("Enter calendar year (1601 thru 9999): ")
    lines = stdin.split(b'\n')
    line = lines[0] if stdin else b''
    if line.endswith(b'\r'):
        line = line[:-1]
    year_s = _move_alnum_to_num(line, 4)
    year = int(year_s)
    if 1601 <= year <= 9999:
        out.append("Year " + year_s + " ")
        if _is_leap(year):
            out.append("is a leap year\n")
        else:
            out.append("is NOT a leap year\n")
    else:
        out.append("Input date is not within range\n")
    return ''.join(out).encode('latin-1'), {}

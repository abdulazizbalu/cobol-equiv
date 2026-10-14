def _move_alnum_to_display(src: bytes, size: int) -> bytearray:
    """Emulates GnuCOBOL's move of alphanumeric data into an unsigned PIC 9(size) field."""
    dst = bytearray(b'0' * size)
    s = 0
    e = len(src)
    while s < e and chr(src[s]).isspace():
        s += 1
    if s != e and src[s] in (ord('+'), ord('-')):
        s += 1
    count = 0
    p = s
    while p < e and src[p] != ord('.'):
        if 48 <= src[p] <= 57:
            count += 1
        p += 1
    d = 0
    if count < size:
        d = size - count
    else:
        while count > size:
            count -= 1
            while True:
                c = src[s]
                s += 1
                if 48 <= c <= 57:
                    break
    seen_dot = 0
    while s < e and d < size:
        c = src[s]
        if 48 <= c <= 57:
            dst[d] = c
            d += 1
        elif c == ord('.'):
            if seen_dot > 0:
                break
            seen_dot += 1
        elif not (chr(c).isspace() or c == ord(',')):
            dst[d] = c
            d += 1
        s += 1
    return dst


def _value(field: bytes) -> int:
    v = 0
    for c in field:
        v = v * 10 + (c & 0x0F)
    return v


def _is_leap(y: int) -> bool:
    return (y % 4 == 0 and y % 100 != 0) or y % 400 == 0


def main(stdin: bytes, input_files: dict) -> tuple:
    out = bytearray()
    out += b"Enter calendar year (1601 thru 9999): "
    field = bytearray(b"0000")
    if stdin:
        line = stdin.split(b"\n", 1)[0]
        if line.endswith(b"\r"):
            line = line[:-1]
        field = _move_alnum_to_display(line, 4)
    year = _value(field)
    if 1601 <= year <= 9999:
        out += b"Year " + bytes(field) + b" "
        if _is_leap(year):
            out += b"is a leap year\n"
        else:
            out += b"is NOT a leap year\n"
    else:
        out += b"Input date is not within range\n"
    return bytes(out), {}

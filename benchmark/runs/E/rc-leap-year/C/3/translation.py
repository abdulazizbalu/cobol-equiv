def _move_alnum_to_num(data: bytes, digits: int) -> bytes:
    # Emulates GnuCOBOL's MOVE from alphanumeric to an unsigned numeric DISPLAY field
    s = data
    b = 0
    e = len(s)
    while b < e and s[b] == 0x20:
        b += 1
    while b < e and s[e - 1] == 0x20:
        e -= 1
    if b < e and s[b] in (0x2B, 0x2D):
        b += 1
    count = 0
    p = b
    while p < e and s[p] != 0x2E:
        count += 1
        p += 1
    size = min(count, digits)
    out = bytearray(b"0" * digits)
    start = b + count - size
    for i in range(size):
        c = s[start + i]
        if 0x30 <= c <= 0x39:
            out[digits - size + i] = c
        else:
            out[digits - size + i] = 0x30 + (c & 0x0F)
    return bytes(out)


def _digit_value(field: bytes) -> int:
    v = 0
    for c in field:
        v = v * 10 + ((c - 0x30) & 0x0F if 0x30 <= c <= 0x39 else (c & 0x0F))
    return v


def main(stdin: bytes, input_files: dict) -> tuple:
    out = bytearray()
    out += b"Enter calendar year (1601 thru 9999): "
    field = b"0000"
    if stdin:
        line = stdin.split(b"\n", 1)[0]
        if line.endswith(b"\r"):
            line = line[:-1]
        if len(line) > 4:
            line = line[:4]
        field = _move_alnum_to_num(line, 4)
    year = _digit_value(field)
    if 1601 <= year <= 9999:
        leap = (year % 4 == 0 and year % 100 != 0) or year % 400 == 0
        out += b"Year " + field + b" "
        if leap:
            out += b"is a leap year\n"
        else:
            out += b"is NOT a leap year\n"
    else:
        out += b"Input date is not within range\n"
    return bytes(out), {}

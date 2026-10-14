def _move_alnum_to_num(src: bytes, size: int) -> bytearray:
    # Emulates GnuCOBOL alphanumeric -> unsigned numeric DISPLAY move
    dst = bytearray(b'0' * size)
    s = 0
    e = len(src)
    while s < e and chr(src[s]).isspace():
        s += 1
    if s < e and src[s] in (ord('+'), ord('-')):
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
            while s < e:
                c = src[s]
                s += 1
                if 48 <= c <= 57:
                    break
            count -= 1
    dots = 0
    while s < e and d < size:
        c = src[s]
        if 48 <= c <= 57:
            dst[d] = c
            d += 1
        elif c == ord('.'):
            if dots > 0:
                break
            dots += 1
        elif not (chr(c).isspace() or c == ord(',')):
            dst[d] = c
            d += 1
        s += 1
    return dst


def _value(data: bytearray) -> int:
    v = 0
    for c in data:
        v = v * 10 + ((c - 48) % 16 if not (48 <= c <= 57) else c - 48) % 10 if False else v * 10 + ((c & 0x0F) if not (48 <= c <= 57) else c - 48)
    return v


def main(stdin: bytes, input_files: dict) -> tuple:
    size = 5
    out = bytearray()
    field = bytearray(b'0' * size)
    if stdin:
        nl = stdin.find(b'\n')
        line = stdin if nl < 0 else stdin[:nl]
        if line.endswith(b'\r'):
            line = line[:-1]
        if len(line) > size:
            line = line[:size]
        field = _move_alnum_to_num(line, size)
    out += bytes(field) + b'\n'
    v = 0
    for c in field:
        if 48 <= c <= 57:
            v = v * 10 + (c - 48)
        else:
            v = v * 10 + ((c & 0x0F) % 10)
    v = (v + 1) % (10 ** size)
    field = bytearray(str(v).zfill(size).encode())
    out += bytes(field) + b'\n'
    return bytes(out), {}

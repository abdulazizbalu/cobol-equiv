def _move_alnum_to_num(src: bytes, size: int) -> bytearray:
    out = bytearray(b'0' * size)
    s1 = 0
    e1 = len(src)
    while s1 < e1 and chr(src[s1]).isspace():
        s1 += 1
    if s1 != e1 and src[s1] in (ord('+'), ord('-')):
        s1 += 1
    count = 0
    p = s1
    while p < e1 and src[p] != ord('.'):
        if 48 <= src[p] <= 57:
            count += 1
        p += 1
    s2 = 0
    if count < size:
        s2 = size - count
    else:
        while count > size:
            count -= 1
            while True:
                c = src[s1]
                s1 += 1
                if 48 <= c <= 57:
                    break
    dots = 0
    while s1 < e1 and s2 < size:
        c = src[s1]
        if 48 <= c <= 57:
            out[s2] = c
            s2 += 1
        elif c == ord('.'):
            if dots > 0:
                break
            dots += 1
        elif not (chr(c).isspace() or c == ord(',')):
            break
        s1 += 1
    return out


def main(stdin: bytes, input_files: dict) -> tuple:
    size = 5
    field = bytearray(b'0' * size)
    if stdin:
        nl = stdin.find(b'\n')
        line = stdin if nl < 0 else stdin[:nl]
        if line.endswith(b'\r'):
            line = line[:-1]
        line = line[:size]
        field = _move_alnum_to_num(line, size)
    out = bytearray()
    out += bytes(field) + b'\n'
    val = 0
    for c in field:
        d = c - 48 if 48 <= c <= 57 else (c & 0x0F) % 10
        val = val * 10 + d
    val = (val + 1) % (10 ** size)
    field = bytearray(str(val).zfill(size).encode())
    out += bytes(field) + b'\n'
    return bytes(out), {}

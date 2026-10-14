def _move_alnum_to_num(src: bytes, size: int) -> bytes:
    dst = bytearray(b'0' * size)
    s1 = 0
    e1 = len(src)
    while s1 < e1 and src[s1:s1 + 1].isspace():
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
            dst[s2] = c
            s2 += 1
        elif c == ord('.'):
            if dots > 0:
                break
            dots += 1
        elif not (bytes([c]).isspace() or c == ord(',')):
            dst[s2] = c
            s2 += 1
        s1 += 1
    return bytes(dst)


def main(stdin: bytes, input_files: dict) -> tuple:
    lines = stdin.split(b'\n')
    has_trailing = stdin.endswith(b'\n')
    if has_trailing:
        lines = lines[:-1]
    if stdin == b'':
        lines = []
    idx = 0

    def accept(cur):
        nonlocal idx
        if idx >= len(lines):
            return cur
        line = lines[idx]
        idx += 1
        if line.endswith(b'\r'):
            line = line[:-1]
        return _move_alnum_to_num(line, 10)

    out = bytearray()
    a = b'0' * 10
    b = b'0' * 10
    out += b'First number: '
    a = accept(a)
    out += b'Second number: '
    b = accept(b)

    if a < b:
        out += a + b' is less than ' + b + b'\n'
    elif a == b:
        out += a + b' is equal to ' + b + b'\n'
    elif a > b:
        out += a + b' is larger than ' + b + b'\n'
    return bytes(out), {}

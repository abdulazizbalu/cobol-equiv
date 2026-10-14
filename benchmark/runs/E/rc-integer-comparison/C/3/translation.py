def _move_alnum_to_num(src: bytes, size: int) -> bytes:
    # Emulates GnuCOBOL cob_move_alphanum_to_display for an unsigned PIC 9(size)
    s1 = 0
    e1 = len(src)
    out = bytearray(b'0' * size)
    spaces = b' \t\n\v\f\r'
    while s1 < e1 and src[s1] in spaces:
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
        elif not (c in spaces or c == ord(',')):
            break
        s1 += 1
    return bytes(out)


def main(stdin: bytes, input_files: dict) -> tuple:
    lines = stdin.split(b'\n')
    if stdin.endswith(b'\n'):
        lines = lines[:-1]
    idx = [0]

    def accept(cur: bytes, size: int) -> bytes:
        if idx[0] >= len(lines):
            return cur
        line = lines[idx[0]]
        idx[0] += 1
        if line.endswith(b'\r'):
            line = line[:-1]
        if len(line) > size:
            line = line[:size]
        return _move_alnum_to_num(line, size)

    out = bytearray()
    a = b'0' * 10
    b = b'0' * 10
    out += b"First number: "
    a = accept(a, 10)
    out += b"Second number: "
    b = accept(b, 10)
    ia = int(a)
    ib = int(b)
    if ia < ib:
        out += a + b" is less than " + b + b"\n"
    elif ia == ib:
        out += a + b" is equal to " + b + b"\n"
    elif ia > ib:
        out += a + b" is larger than " + b + b"\n"
    return bytes(out), {}

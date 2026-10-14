def _move_alnum_to_display(src: bytes, size: int) -> bytearray:
    # Emulates GnuCOBOL cob_move_alphanum_to_display for an unsigned
    # integer DISPLAY field of `size` digits.
    dst = bytearray(b'0' * size)
    s1 = 0
    e1 = len(src)
    dec_pt = ord('.')
    num_sep = ord(',')

    def isspace(c):
        return c in (0x20, 0x09, 0x0a, 0x0b, 0x0c, 0x0d)

    def isdigit(c):
        return 0x30 <= c <= 0x39

    while s1 < e1 and isspace(src[s1]):
        s1 += 1

    if s1 != e1 and src[s1] in (ord('+'), ord('-')):
        s1 += 1

    count = 0
    p = s1
    while p < e1 and src[p] != dec_pt:
        if isdigit(src[p]):
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
                if isdigit(c):
                    break

    cnt = 0
    while s1 < e1 and s2 < size:
        c = src[s1]
        if isdigit(c):
            dst[s2] = c
            s2 += 1
        elif c == dec_pt:
            if cnt > 0:
                break
            cnt += 1
        elif not (isspace(c) or c == num_sep):
            break
        s1 += 1
    return dst


def main(stdin: bytes, input_files: dict) -> tuple:
    out = []
    num = bytearray(b'00000')
    if stdin:
        line = stdin.split(b'\n', 1)[0]
        if line.endswith(b'\r'):
            line = line[:-1]
        num = _move_alnum_to_display(line, 5)
    out.append(bytes(num) + b'\n')
    val = (int(num.decode('ascii')) + 1) % 100000
    num = bytearray(('%05d' % val).encode('ascii'))
    out.append(bytes(num) + b'\n')
    return b''.join(out), {}

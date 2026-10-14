def _move_alnum_to_display(src: bytes, int_digits: int, scale: int) -> bytes:
    size = int_digits + scale
    out = bytearray(b'0' * size)
    s1 = 0
    e1 = len(src)
    dec_pt = ord('.')
    num_sep = ord(',')

    def isdigit(c):
        return 48 <= c <= 57

    def isspace(c):
        return c in (32, 9, 10, 11, 12, 13)

    # Skip white spaces
    while s1 < e1 and isspace(src[s1]):
        s1 += 1
    # Check for sign
    if s1 != e1 and src[s1] in (ord('+'), ord('-')):
        s1 += 1
    # Count digits before decimal point
    count = 0
    p = s1
    while p < e1 and src[p] != dec_pt:
        if isdigit(src[p]):
            count += 1
        p += 1
    s2 = 0
    if count < int_digits:
        s2 += int_digits - count
    else:
        while count > int_digits:
            count -= 1
            while True:
                c = src[s1]
                s1 += 1
                if isdigit(c):
                    break
    # Move
    count = 0
    while s1 < e1 and s2 < size:
        c = src[s1]
        if isdigit(c):
            out[s2] = c
            s2 += 1
        elif c == dec_pt:
            if count > 0:
                break
            count += 1
        elif not (isspace(c) or c == num_sep):
            break
        s1 += 1
    return bytes(out)


def main(stdin: bytes, input_files: dict) -> tuple:
    lines = stdin.split(b'\n')
    if stdin == b'':
        line = b''
    else:
        line = lines[0]
    data = _move_alnum_to_display(line, 5, 3)
    out = data[:5] + b'.' + data[5:] + b'\n'
    return out, {}

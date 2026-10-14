def _move_alnum_to_num7(src: bytes) -> str:
    # Emulates GnuCOBOL cob_move_alphanum_to_display into PIC 9(7)
    size = 7
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
            while s1 < e1:
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
            out[s2] = c
            s2 += 1
        s1 += 1
    return out.decode('latin-1')


def main(stdin: bytes, input_files: dict) -> tuple:
    lines = stdin.split(b'\n')
    line = lines[0] if lines else b''
    if line.endswith(b'\r'):
        line = line[:-1]
    nstr = (line[:7] + b' ' * 7)[:7]
    digits = _move_alnum_to_num7(nstr)
    n = 0
    for ch in digits:
        n = n * 10 + ((ord(ch) & 0x0F) % 10)
    binary_number = ' ' * 21
    while n != 0:
        q, r = divmod(n, 2)
        n = q
        d = str(r)
        idx = binary_number.find(' ')
        part = binary_number if idx < 0 else binary_number[:idx]
        new = d + part
        if len(new) > 21:
            new = new[:21]
        # STRING does not clear str beyond written part; previous str was
        # binary_number, which new always covers (or equals in length).
        str_val = new + binary_number[len(new):] if len(new) < 21 else new
        binary_number = str_val
    out = (binary_number + '\n').encode('latin-1')
    return out, {}

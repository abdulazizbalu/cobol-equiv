def main(stdin: bytes, input_files: dict) -> tuple:
    FSIZE = 8
    SCALE = 3
    field = bytearray(b'0' * FSIZE)

    # Read one line
    if len(stdin) > 0:
        nl = stdin.find(b'\n')
        line = stdin if nl < 0 else stdin[:nl]
        # numeric display: truncate to field size
        if len(line) > FSIZE:
            line = line[:FSIZE]
        src = line
        dec_pt = ord('.')
        num_sep = ord(',')

        def isspace(c):
            return c in (0x20, 0x09, 0x0a, 0x0b, 0x0c, 0x0d)

        def isdigit(c):
            return 0x30 <= c <= 0x39

        s1 = 0
        e1 = len(src)
        s2 = 0
        e2 = FSIZE
        field = bytearray(b'0' * FSIZE)
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
        size = FSIZE - SCALE
        if count < size:
            s2 += size - count
        else:
            while count > size:
                count -= 1
                while True:
                    c = src[s1] if s1 < e1 else 0
                    s1 += 1
                    if isdigit(c):
                        break
        count = 0
        while s1 < e1 and s2 < e2:
            c = src[s1]
            if isdigit(c):
                field[s2] = c
                s2 += 1
            elif c == dec_pt:
                if count > 0:
                    count += 1
                    break
                count += 1
            elif not (isspace(c) or c == num_sep):
                break
            s1 += 1

    out = bytes(field[:FSIZE - SCALE]) + b'.' + bytes(field[FSIZE - SCALE:]) + b'\n'
    return out, {}

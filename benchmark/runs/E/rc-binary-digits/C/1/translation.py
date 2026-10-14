def _alnum_to_display(src: bytes, size: int) -> bytes:
    out = bytearray(b'0' * size)
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
            count -= 1
            while s < e:
                c = src[s]
                s += 1
                if 48 <= c <= 57:
                    break
    seen_dot = 0
    while s < e and d < size:
        c = src[s]
        if 48 <= c <= 57:
            out[d] = c
            d += 1
        elif c == ord('.'):
            if seen_dot > 0:
                break
            seen_dot += 1
        elif not (chr(c).isspace() or c == ord(',')):
            out[d] = c
            d += 1
        s += 1
    return bytes(out)


def main(stdin: bytes, input_files: dict) -> tuple:
    lines = stdin.split(b'\n')
    nstr = b' ' * 7
    if stdin:
        line = lines[0]
        if line.endswith(b'\r'):
            line = line[:-1]
        nstr = (line + b' ' * 7)[:7]
    ndisp = _alnum_to_display(nstr, 7)
    n = 0
    for c in ndisp:
        n = n * 10 + (c & 0x0F if c >= 48 else 0) % 10
    binary_number = bytearray(b' ' * 21)
    s = bytearray(b' ' * 21)
    while n != 0:
        digit = n % 2
        n //= 2
        bd = bytes([48 + digit])
        bn = bytes(binary_number)
        idx = bn.find(b' ')
        part = bn if idx < 0 else bn[:idx]
        data = bd + part
        data = data[:21]
        s[:len(data)] = data
        binary_number = bytearray(s)
    out = bytes(binary_number) + b'\n'
    return out, {}

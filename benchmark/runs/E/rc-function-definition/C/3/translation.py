def _accept_numeric(line: bytes, size: int) -> bytes:
    dst = bytearray(b'0' * size)
    s = line
    n = len(s)
    i = 0
    while i < n and chr(s[i]).isspace():
        i += 1
    if i < n and s[i] in (ord('+'), ord('-')):
        i += 1
    count = 0
    p = i
    while p < n and s[p] != ord('.'):
        if 48 <= s[p] <= 57:
            count += 1
        p += 1
    d = 0
    if count < size:
        d = size - count
    else:
        while count > size:
            count -= 1
            while True:
                if i >= n:
                    break
                c = s[i]
                i += 1
                if 48 <= c <= 57:
                    break
    dots = 0
    while i < n and d < size:
        c = s[i]
        if 48 <= c <= 57:
            dst[d] = c
            d += 1
        elif c == ord('.'):
            if dots > 0:
                break
            dots += 1
        elif not (chr(c).isspace() or c == ord(',')):
            break
        i += 1
    return bytes(dst)


def main(stdin: bytes, input_files: dict) -> tuple:
    lines = stdin.split(b'\n')
    if stdin.endswith(b'\n'):
        lines = lines[:-1]
    pos = 0
    x = b'000'
    y = b'000'
    if pos < len(lines):
        ln = lines[pos].rstrip(b'\r')
        pos += 1
        x = _accept_numeric(ln, 3)
    if pos < len(lines):
        ln = lines[pos].rstrip(b'\r')
        pos += 1
        y = _accept_numeric(ln, 3)
    z = (int(x) * int(y)) % 10 ** 9
    out = ('%09d' % z).encode() + b'\n'
    return out, {}

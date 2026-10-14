def _accept_numeric(line: bytes, size: int) -> int:
    # Emulates GnuCOBOL move of alphanumeric data to an unsigned
    # numeric DISPLAY field (scale 0).
    data = bytearray(b'0' * size)
    s = line
    i = 0
    n = len(s)

    def isspace(c):
        return c in b' \t\n\r\x0b\x0c'

    def isdigit(c):
        return 48 <= c <= 57

    while i < n and isspace(s[i]):
        i += 1
    if i < n and s[i] in b'+-':
        i += 1
    count = 0
    p = i
    while p < n and s[p] != ord('.'):
        if isdigit(s[p]):
            count += 1
        p += 1
    pos = 0
    if count < size:
        pos = size - count
    else:
        while count > size:
            count -= 1
            while i < n:
                c = s[i]
                i += 1
                if isdigit(c):
                    break
    dots = 0
    while i < n and pos < size:
        c = s[i]
        if isdigit(c):
            data[pos] = c
            pos += 1
        elif c == ord('.'):
            if dots > 0:
                break
            dots += 1
        elif not (isspace(c) or c == ord(',')):
            break
        i += 1
    return int(data.decode('ascii'))


def main(stdin: bytes, input_files: dict) -> tuple:
    lines = stdin.split(b'\n')
    if stdin.endswith(b'\n'):
        lines = lines[:-1]
    idx = 0
    x = 0
    y = 0
    if idx < len(lines):
        x = _accept_numeric(lines[idx].rstrip(b'\r'), 3)
        idx += 1
    if idx < len(lines):
        y = _accept_numeric(lines[idx].rstrip(b'\r'), 3)
        idx += 1
    z = (x * y) % 1000000000
    out = ('%09d\n' % z).encode('ascii')
    return out, {}

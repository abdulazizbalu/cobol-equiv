def _parse(line: bytes, size: int = 5):
    s = line
    n = len(s)
    i = 0
    while i < n and chr(s[i]).isspace():
        i += 1
    sign = 1
    if i < n and s[i] in (ord('+'), ord('-')):
        sign = 1 if s[i] == ord('+') else -1
        i += 1
    count = 0
    p = i
    while p < n and s[p] != ord('.'):
        if 48 <= s[p] <= 57:
            count += 1
        p += 1
    out = ['0'] * size
    pos = 0
    if count < size:
        pos = size - count
    else:
        while count > size:
            count -= 1
            while i < n:
                c = s[i]
                i += 1
                if 48 <= c <= 57:
                    break
    dots = 0
    while i < n and pos < size:
        c = s[i]
        if 48 <= c <= 57:
            out[pos] = chr(c)
            pos += 1
        elif c == ord('.'):
            if dots > 0:
                break
            dots += 1
        elif not (chr(c).isspace() or c == ord(',')):
            break
        i += 1
    return sign * int(''.join(out))


def main(stdin: bytes, input_files: dict) -> tuple:
    lines = stdin.split(b'\n')
    if lines and lines[-1] == b'':
        lines = lines[:-1]

    def get(k):
        if k < len(lines):
            l = lines[k]
            if l.endswith(b'\r'):
                l = l[:-1]
            return l
        return b''

    a = _parse(get(0))
    b = _parse(get(1))
    s = a + b
    neg = s < 0
    mag = abs(s) % 100000
    out = ('-' if neg else '+') + '%05d' % mag + '\n'
    return out.encode(), {}

def _accept_numeric(line: bytes, size: int = 5) -> int:
    # Emulates ACCEPT into a PIC S9(5) DISPLAY field
    data = line
    if len(data) > size:
        data = data[:size]
    i = 0
    n = len(data)
    while i < n and data[i:i + 1].isspace():
        i += 1
    sign = 1
    if i < n and data[i:i + 1] in (b'+', b'-'):
        if data[i:i + 1] == b'-':
            sign = -1
        i += 1
    p = i
    while p < n and data[p:p + 1] != b'.':
        p += 1
    intpart = data[i:p]
    digits = []
    for c in intpart:
        d = c & 0x0F
        if d > 9:
            d = d % 10
        digits.append(d)
    digits = digits[-size:]
    val = 0
    for d in digits:
        val = val * 10 + d
    return sign * val


def main(stdin: bytes, input_files: dict) -> tuple:
    lines = stdin.split(b'\n')
    if lines and lines[-1] == b'':
        lines = lines[:-1]
    idx = 0
    a = 0
    b = 0
    if idx < len(lines):
        a = _accept_numeric(lines[idx].rstrip(b'\r'))
        idx += 1
    if idx < len(lines):
        b = _accept_numeric(lines[idx].rstrip(b'\r'))
        idx += 1
    s = a + b
    neg = s < 0
    mag = abs(s) % 100000
    if mag == 0:
        neg = False
    out = ('-' if neg else '+') + '%05d' % mag + '\n'
    return out.encode('ascii'), {}

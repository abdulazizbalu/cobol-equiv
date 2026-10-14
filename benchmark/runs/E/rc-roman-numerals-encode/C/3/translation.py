def _accept_numeric(line: bytes, size: int) -> bytes:
    """Emulate the GnuCOBOL move of an alphanumeric value into an unsigned PIC 9(size) field."""
    s = line
    n = len(s)
    out = bytearray(b'0' * size)
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
    pos = 0
    if count < size:
        pos = size - count
    else:
        while count > size:
            count -= 1
            while i < n and not (48 <= s[i] <= 57):
                i += 1
            i += 1
    dots = 0
    while i < n and pos < size:
        c = s[i]
        if 48 <= c <= 57:
            out[pos] = c
            pos += 1
        elif c == ord('.'):
            if dots > 0:
                break
            dots += 1
        elif not (chr(c).isspace() or c == ord(',')):
            out[pos] = c
            pos += 1
        i += 1
    return bytes(out)


def _value(data: bytes) -> int:
    v = 0
    for c in data:
        v = v * 10 + (c & 0x0F)
    return v


TABLE = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"),
    (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"),
    (5, "V"), (4, "IV"), (1, "I"),
]


def main(stdin: bytes, input_files: dict) -> tuple:
    lines = stdin.split(b'\n')
    if stdin.endswith(b'\n'):
        lines = lines[:-1]
    idx = 0
    out = []

    def accept():
        nonlocal idx
        if idx >= len(lines):
            return None
        l = lines[idx]
        idx += 1
        return _accept_numeric(l, 4)

    data = accept()
    if data is None:
        data = b'0000'
    while True:
        num = _value(data)
        if num == 0:
            break
        save = data
        if 0 < num < 4000:
            roman = ""
            for div, ch in TABLE:
                if num == 0:
                    break
                while num >= div:
                    roman += ch
                    num -= div
            out.append(b'inp=' + save + b' roman=' + roman.ljust(16).encode())
            data = b'%04d' % num
        else:
            out.append(b'inp=' + save + b' invalid')
        nd = accept()
        if nd is None:
            break
        data = nd
    res = b''.join(x + b'\n' for x in out)
    return res, {}

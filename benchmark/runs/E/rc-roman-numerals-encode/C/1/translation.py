def _accept_numeric(line: bytes, size: int) -> int:
    # GnuCOBOL: input truncated to field size for numeric display, then
    # moved as alphanumeric to numeric display.
    data = line[:size]
    n = len(data)
    i = 0
    while i < n and chr(data[i]).isspace():
        i += 1
    if i < n and data[i] in (ord('+'), ord('-')):
        i += 1
    # count digits before decimal point
    count = 0
    p = i
    while p < n and data[p] != ord('.'):
        if 48 <= data[p] <= 57:
            count += 1
        p += 1
    out = ['0'] * size
    pos = 0
    if count < size:
        pos = size - count
    else:
        while count > size:
            count -= 1
            while True:
                c = data[i]
                i += 1
                if 48 <= c <= 57:
                    break
    dots = 0
    while i < n and pos < size:
        c = data[i]
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
    return int(''.join(out))


TABLE = [
    (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'),
    (90, 'XC'), (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'),
    (5, 'V'), (4, 'IV'), (1, 'I'),
]


def main(stdin: bytes, input_files):
    lines = stdin.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
    idx = [0]

    def accept():
        if idx[0] < len(lines):
            ln = lines[idx[0]]
            idx[0] += 1
            if ln.endswith(b'\r'):
                ln = ln[:-1]
            return _accept_numeric(ln, 4)
        return 0

    out = []
    num = accept()
    while num != 0:
        save = num
        if 0 < num < 4000:
            roman = ''
            for div, ch in TABLE:
                if num == 0:
                    break
                while num >= div:
                    roman += ch
                    num -= div
            roman = roman[:16].ljust(16)
            out.append('inp=%04d roman=%s\n' % (save, roman))
        else:
            out.append('inp=%04d invalid\n' % save)
        num = accept()
    return ''.join(out).encode('latin-1'), {}

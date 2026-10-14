def _alnum_to_num(src: bytes, size: int) -> int:
    """Emulates GnuCOBOL's MOVE of an alphanumeric field to an unsigned
    numeric DISPLAY field with no decimal places."""
    out = bytearray(b'0' * size)
    s = 0
    e = len(src)
    # Skip leading white space
    while s < e and chr(src[s]).isspace():
        s += 1
    # Optional sign (ignored for an unsigned target)
    if s < e and src[s] in (ord('+'), ord('-')):
        s += 1
    # Count the digits before the decimal point
    count = 0
    p = s
    while p < e and src[p] != ord('.'):
        if 48 <= src[p] <= 57:
            count += 1
        p += 1
    # Right-align the integer part; drop excess high-order digits
    pos = 0
    if count < size:
        pos = size - count
    else:
        while count > size:
            while s < e:
                c = src[s]
                s += 1
                if 48 <= c <= 57:
                    break
            count -= 1
    # Copy digits, stopping at the decimal point or an invalid character
    while s < e and pos < size:
        c = src[s]
        if 48 <= c <= 57:
            out[pos] = c
            pos += 1
        elif c == ord('.'):
            break
        elif chr(c).isspace() or c == ord(','):
            pass
        else:
            break
        s += 1
    return int(out.decode('ascii'))


def main(stdin: bytes, input_files: dict) -> tuple:
    # ACCEPT nstr: read one line into PIC X(7), padded with spaces
    nstr = b' ' * 7
    if stdin:
        line = stdin.split(b'\n', 1)[0]
        if line.endswith(b'\r'):
            line = line[:-1]
        nstr = (line + b' ' * 7)[:7]

    n = _alnum_to_num(nstr, 7)

    binary_number = bytearray(b' ' * 21)
    s = bytearray(b' ' * 21)

    while n != 0:
        n, digit = divmod(n, 2)
        bd = bytes([48 + digit])
        # STRING bd DELIMITED BY SIZE, binary_number DELIMITED BY SPACE INTO str
        idx = binary_number.find(b' ')
        part = bytes(binary_number) if idx < 0 else bytes(binary_number[:idx])
        data = (bd + part)[:21]
        s[0:len(data)] = data
        # MOVE str TO binary_number
        binary_number = bytearray(s)

    out = bytes(binary_number) + b'\n'
    return out, {}

def _accept_numeric(line: bytes, size: int) -> int:
    # Emulates GnuCOBOL moving an alphanumeric value into an unsigned
    # PIC 9(size) DISPLAY field.
    spaces = b" \t\n\v\f\r"
    digits = b"0123456789"
    dec_pt = ord(".")
    num_sep = ord(",")
    dst = bytearray(b"0" * size)
    s1 = 0
    e1 = len(line)
    while s1 < e1 and line[s1] in spaces:
        s1 += 1
    if s1 < e1 and line[s1] in b"+-":
        s1 += 1
    count = 0
    p = s1
    while p < e1 and line[p] != dec_pt:
        if line[p] in digits:
            count += 1
        p += 1
    s2 = 0
    if count < size:
        s2 = size - count
    else:
        while count > size:
            count -= 1
            while True:
                c = line[s1]
                s1 += 1
                if c in digits:
                    break
    seen_pt = 0
    while s1 < e1 and s2 < size:
        c = line[s1]
        if c in digits:
            dst[s2] = c
            s2 += 1
        elif c == dec_pt:
            if seen_pt > 0:
                break
            seen_pt += 1
        elif not (c in spaces or c == num_sep):
            break
        s1 += 1
    return int(dst.decode("ascii"))


def main(stdin: bytes, input_files: dict) -> tuple:
    lines = stdin.split(b"\n")
    if stdin.endswith(b"\n"):
        lines = lines[:-1]
    idx = 0
    out = []

    def accept(cur):
        nonlocal idx
        if idx < len(lines):
            line = lines[idx]
            idx += 1
            return _accept_numeric(line, 10)
        return cur

    a = 0
    b = 0
    temp = 0
    out.append(b"Enter first number, max 10 digits.\n")
    a = accept(a)
    out.append(b"Enter second number, max 10 digits.\n")
    b = accept(b)
    if a < b:
        temp = b
        b = a
        b = temp
    while b != 0:
        temp = a
        a = b
        dividend = temp
        q = dividend // b
        r = dividend - q * b
        temp = q % (10 ** 10)
        b = r % (10 ** 10)
    out.append(b"The gcd is " + ("%010d" % a).encode("ascii") + b"\n")
    return b"".join(out), {}

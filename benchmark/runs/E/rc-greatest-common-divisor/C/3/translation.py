def _accept_numeric(line: bytes, size: int = 10) -> bytearray:
    s = line
    e1 = len(s)
    out = bytearray(b"0" * size)
    i = 0
    while i < e1 and chr(s[i]).isspace():
        i += 1
    if i < e1 and s[i] in (ord("+"), ord("-")):
        i += 1
    count = 0
    p = i
    while p < e1 and s[p] != ord("."):
        if 48 <= s[p] <= 57:
            count += 1
        p += 1
    s2 = 0
    if count < size:
        s2 = size - count
    else:
        while count > size:
            count -= 1
            while True:
                c = s[i]
                i += 1
                if 48 <= c <= 57:
                    break
    dots = 0
    while i < e1 and s2 < size:
        c = s[i]
        if 48 <= c <= 57:
            out[s2] = c
            s2 += 1
        elif c == ord("."):
            if dots > 0:
                break
            dots += 1
        elif not (chr(c).isspace() or c == ord(",")):
            out[s2] = c
            s2 += 1
        i += 1
    return out


def _val(field: bytes) -> int:
    v = 0
    for c in field:
        v = v * 10 + (c & 0x0F if not (48 <= c <= 57) else c - 48) % 10
    return v


def main(stdin: bytes, input_files: dict) -> tuple:
    lines = stdin.split(b"\n")
    if lines and lines[-1] == b"" and stdin.endswith(b"\n"):
        lines = lines[:-1]
    idx = 0

    def accept():
        nonlocal idx
        if idx < len(lines):
            l = lines[idx]
            idx += 1
            return _accept_numeric(l)
        return None

    out = []
    a_raw = bytearray(b"0" * 10)
    b_raw = bytearray(b"0" * 10)
    out.append(b"Enter first number, max 10 digits.\n")
    r = accept()
    if r is not None:
        a_raw = r
    out.append(b"Enter second number, max 10 digits.\n")
    r = accept()
    if r is not None:
        b_raw = r

    a = _val(a_raw)
    b = _val(b_raw)
    computed = False
    while b != 0:
        temp = a
        a = b
        q = (temp // b) % 10**10
        b = (temp - q * b) % 10**10
        computed = True

    if computed:
        a_bytes = ("%010d" % a).encode()
    else:
        a_bytes = bytes(a_raw)
    out.append(b"The gcd is " + a_bytes + b"\n")
    return b"".join(out), {}

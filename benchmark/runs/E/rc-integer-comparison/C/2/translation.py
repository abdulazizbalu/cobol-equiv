def _isspace(c):
    return c in b" \t\n\v\f\r"


def _isdigit(c):
    return 48 <= c <= 57


def _move_alnum_to_num(data: bytes, size: int) -> bytes:
    out = bytearray(b"0" * size)
    n = len(data)
    i = 0
    while i < n and _isspace(data[i]):
        i += 1
    if i < n and data[i] in (ord("+"), ord("-")):
        i += 1
    dec_pt = ord(".")
    num_sep = ord(",")
    count = 0
    p = i
    while p < n and data[p] != dec_pt:
        if _isdigit(data[p]):
            count += 1
        p += 1
    s2 = 0
    if count < size:
        s2 = size - count
    else:
        while count > size:
            count -= 1
            while True:
                c = data[i] if i < n else 0
                i += 1
                if _isdigit(c):
                    break
    cnt = 0
    while i < n and s2 < size:
        c = data[i]
        if _isdigit(c):
            out[s2] = c
            s2 += 1
        elif c == dec_pt:
            if cnt > 0:
                break
            cnt += 1
        elif not (_isspace(c) or c == num_sep):
            break
        i += 1
    return bytes(out)


def main(stdin: bytes, input_files: dict) -> tuple:
    lines = stdin.split(b"\n")
    if stdin.endswith(b"\n"):
        lines = lines[:-1]
    pos = [0]

    def accept():
        if pos[0] < len(lines):
            l = lines[pos[0]]
            pos[0] += 1
            return l
        return b""

    out = bytearray()
    out += b"First number: "
    a = _move_alnum_to_num(accept(), 10)
    out += b"Second number: "
    b = _move_alnum_to_num(accept(), 10)
    ia, ib = int(a), int(b)
    if ia < ib:
        out += a + b" is less than " + b + b"\n"
    elif ia == ib:
        out += a + b" is equal to " + b + b"\n"
    elif ia > ib:
        out += a + b" is larger than " + b + b"\n"
    return bytes(out), {}

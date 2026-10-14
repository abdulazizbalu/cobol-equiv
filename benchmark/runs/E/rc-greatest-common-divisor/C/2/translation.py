import sys


def _isspace(c):
    return c in b" \t\n\v\f\r"


def _isdigit(c):
    return 48 <= c <= 57


def _alnum_to_display(src: bytes, size: int = 10) -> bytearray:
    out = bytearray(b"0" * size)
    s1 = 0
    e1 = len(src)
    while s1 < e1 and _isspace(src[s1]):
        s1 += 1
    if s1 < e1 and src[s1] in (ord("+"), ord("-")):
        s1 += 1
    count = 0
    p = s1
    while p < e1 and src[p] != ord("."):
        if _isdigit(src[p]):
            count += 1
        p += 1
    s2 = 0
    if count < size:
        s2 = size - count
    else:
        while count > size:
            count -= 1
            while s1 < e1:
                c = src[s1]
                s1 += 1
                if _isdigit(c):
                    break
    dots = 0
    while s1 < e1 and s2 < size:
        c = src[s1]
        if _isdigit(c):
            out[s2] = c
            s2 += 1
        elif c == ord("."):
            if dots > 0:
                break
            dots += 1
        elif not (_isspace(c) or c == ord(",")):
            out[s2] = c
            s2 += 1
        s1 += 1
    return out


def _value(field: bytearray) -> int:
    v = 0
    for c in field:
        v = v * 10 + ((c - 48) if _isdigit(c) else (c & 0x0F) % 10)
    return v


def _to_field(v: int) -> bytearray:
    v %= 10 ** 10
    return bytearray(b"%010d" % v)


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
            return _alnum_to_display(line)
        return cur

    a = bytearray(b"0" * 10)
    b = bytearray(b"0" * 10)
    temp = bytearray(b"0" * 10)

    out.append(b"Enter first number, max 10 digits.\n")
    a = accept(a)
    out.append(b"Enter second number, max 10 digits.\n")
    b = accept(b)

    if _value(a) < _value(b):
        temp = bytearray(b)
        b = bytearray(a)
        b = bytearray(temp)

    while _value(b) != 0:
        temp = bytearray(a)
        a = bytearray(b)
        t = _value(temp)
        d = _value(b)
        q = t // d
        r = t - q * d
        temp = _to_field(q)
        b = _to_field(r)

    out.append(b"The gcd is " + bytes(a) + b"\n")
    return b"".join(out), {}


if __name__ == "__main__":
    data = sys.stdin.buffer.read()
    o, _ = main(data, {})
    sys.stdout.buffer.write(o)

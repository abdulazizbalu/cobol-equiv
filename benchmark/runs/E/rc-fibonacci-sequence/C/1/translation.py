def _accept_numeric(line: bytes, size: int) -> int:
    # Emulate GnuCOBOL ACCEPT into an unsigned PIC 9(size) DISPLAY field
    data = line[:size]
    dst = [ord('0')] * size
    s1 = 0
    e1 = len(data)
    while s1 < e1 and chr(data[s1]).isspace():
        s1 += 1
    if s1 != e1 and data[s1] in (ord('+'), ord('-')):
        s1 += 1
    count = 0
    p = s1
    while p < e1 and data[p] != ord('.'):
        if 48 <= data[p] <= 57:
            count += 1
        p += 1
    s2 = 0
    if count < size:
        s2 = size - count
    else:
        while count > size:
            count -= 1
            while True:
                c = data[s1]
                s1 += 1
                if 48 <= c <= 57:
                    break
    dots = 0
    while s1 < e1 and s2 < size:
        c = data[s1]
        if 48 <= c <= 57:
            dst[s2] = c
            s2 += 1
        elif c == ord('.'):
            if dots > 0:
                break
            dots += 1
        elif not (chr(c).isspace() or c == ord(',')):
            dst[s2] = c
            s2 += 1
        s1 += 1
    val = 0
    for c in dst:
        val = val * 10 + (c & 0x0F)
    return val % (10 ** size)


def _format(n: int, fr: str) -> str:
    s = str(n).rjust(36)
    fr = s  # MOVE INTERM-RESULT TO FORMATTED-RESULT
    i = s.find(' ')
    if i < 0:
        return fr
    j = i
    while j < len(s) and s[j] == ' ':
        j += 1
    if j >= len(s):
        return fr
    k = s.find(' ', j)
    if k < 0:
        k = len(s)
    field2 = s[j:k]
    return field2[:36].ljust(36)


def main(stdin: bytes, input_files: dict) -> tuple:
    out = []
    out.append(b"What place of the Fibonacci Sequence would you like (<173)? ")
    lines = stdin.split(b"\n")
    line = lines[0] if lines else b""
    if line.endswith(b"\r"):
        line = line[:-1]
    count = _accept_numeric(line, 4)
    MOD = 10 ** 36
    fib = 0
    one = 0
    two = 1
    fr = " " * 36
    if count < 1:
        return b"".join(out), {}
    if count < 2:
        fr = _format(fib, fr)
        out.append(fr.encode("latin-1") + b"\n")
        return b"".join(out), {}
    count = (count - 1) % 10000
    fr = _format(fib, fr)
    out.append(fr.encode("latin-1") + b"\n")
    while count != 0:
        fib = (one + two) % MOD
        one = two
        two = fib
        count = (count - 1) % 10000
        fr = _format(fib, fr)
        out.append(fr.encode("latin-1") + b"\n")
    return b"".join(out), {}

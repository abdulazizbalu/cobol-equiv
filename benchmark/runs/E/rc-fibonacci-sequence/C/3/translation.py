def _accept_numeric(line: bytes, size: int) -> int:
    # Emulates GnuCOBOL's move of alphanumeric data into an unsigned PIC 9(size) field.
    s = line
    i = 0
    n = len(s)
    out = [ord('0')] * size
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
            while i < n:
                c = s[i]
                i += 1
                if 48 <= c <= 57:
                    break
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
            break
        i += 1
    return int(bytes(out).decode())


def main(stdin: bytes, input_files: dict) -> tuple:
    out = []
    out.append(b"What place of the Fibonacci Sequence would you like (<173)? ")
    lines = stdin.split(b"\n")
    count = 0
    if stdin:
        line = lines[0]
        if line.endswith(b"\r"):
            line = line[:-1]
        count = _accept_numeric(line, 4)
    MOD = 10 ** 36

    def disp(v):
        out.append(str(v).ljust(36).encode() + b"\n")

    fib_num = 0
    fib_one = 0
    fib_two = 1
    if count < 1:
        return b"".join(out), {}
    if count < 2:
        disp(fib_num)
        return b"".join(out), {}
    count -= 1
    disp(fib_num)
    while count != 0:
        fib_num = (fib_one + fib_two) % MOD
        fib_one = fib_two
        fib_two = fib_num
        count -= 1
        disp(fib_num)
    return b"".join(out), {}

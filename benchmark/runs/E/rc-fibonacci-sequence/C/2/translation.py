def _accept_numeric(line: bytes, size: int) -> int:
    # Emulates GnuCOBOL move of alphanumeric data into an unsigned PIC 9(size).
    dest = bytearray(b'0' * size)
    s1 = 0
    e1 = len(line)
    spaces = b' \t\n\v\f\r'
    while s1 < e1 and line[s1] in spaces:
        s1 += 1
    if s1 != e1 and line[s1] in b'+-':
        s1 += 1
    count = 0
    p = s1
    while p < e1 and line[p] != ord('.'):
        if 48 <= line[p] <= 57:
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
                if 48 <= c <= 57:
                    break
    dots = 0
    while s1 < e1 and s2 < size:
        c = line[s1]
        if 48 <= c <= 57:
            dest[s2] = c
            s2 += 1
        elif c == ord('.'):
            if dots > 0:
                break
            dots += 1
        elif not (c in spaces or c == ord(',')):
            break
        s1 += 1
    return int(dest.decode('ascii'))


def _fmt(n: int) -> bytes:
    interm = str(n).rjust(36)
    if interm.startswith(' '):
        res = interm.lstrip(' ').ljust(36)
    else:
        res = interm
    return res.encode('ascii') + b'\n'


def main(stdin: bytes, input_files: dict) -> tuple:
    out = bytearray()
    out += b'What place of the Fibonacci Sequence would you like (<173)? '
    MOD = 10 ** 36
    desired = 0
    if stdin:
        idx = stdin.find(b'\n')
        line = stdin if idx < 0 else stdin[:idx]
        desired = _accept_numeric(line, 4)
    if desired < 1:
        return bytes(out), {}
    fib_num = 0
    fib_one = 0
    fib_two = 1
    if desired < 2:
        out += _fmt(fib_num)
        return bytes(out), {}
    desired -= 1
    out += _fmt(fib_num)
    while desired != 0:
        fib_num = (fib_one + fib_two) % MOD
        fib_one = fib_two
        fib_two = fib_num
        desired -= 1
        out += _fmt(fib_num)
    return bytes(out), {}

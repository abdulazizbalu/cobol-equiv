import sys


def _accept_numeric(line: bytes, int_digits: int = 9) -> int:
    """Emulate GnuCOBOL moving an alphanumeric ACCEPT buffer into an
    unsigned PIC 9(n) DISPLAY field."""
    s = line
    n = len(s)
    out = [ord('0')] * int_digits
    i = 0
    # skip leading white space
    while i < n and chr(s[i]).isspace():
        i += 1
    # sign (ignored for an unsigned field)
    if i < n and s[i] in (ord('+'), ord('-')):
        i += 1
    # count digits before the decimal point
    count = 0
    p = i
    while p < n and s[p] != ord('.'):
        if 48 <= s[p] <= 57:
            count += 1
        p += 1
    pos = 0
    if count < int_digits:
        pos = int_digits - count
    else:
        while count > int_digits:
            count -= 1
            while True:
                c = s[i] if i < n else 48
                i += 1
                if 48 <= c <= 57:
                    break
    dots = 0
    while i < n and pos < int_digits:
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
    return int(bytes(out).decode('ascii'))


def _format_output(avg_scaled: int) -> bytes:
    int_part = avg_scaled // 10**9
    frac_part = avg_scaled % 10**9
    int_str = str(int_part % 10**9).rjust(9, ' ')
    return (int_str + '.' + str(frac_part).zfill(9)).encode('ascii')


def main(stdin: bytes, input_files: dict) -> tuple:
    lines = stdin.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
    idx = 0
    avg = 0       # scale 9, PIC 9(9)V9(9)
    amount = 0    # PIC 9(9)
    MAXD = 38
    while True:
        if idx >= len(lines):
            break  # EOF: avoid endless loop
        line = lines[idx]
        idx += 1
        if line.endswith(b'\r'):
            line = line[:-1]
        current = _accept_numeric(line)
        if current == 99999:
            break
        amount = (amount + 1) % 10**9
        if amount == 0:
            continue
        t1 = avg * (amount - 1)                     # scale 9
        q1 = (t1 * 10**MAXD) // amount              # scale 47
        q2 = (current * 10**MAXD) // amount         # scale 38
        total = q1 + q2 * 10**9                     # scale 47
        res = total // 10**MAXD                     # scale 9, truncated
        avg = res % 10**18
    return _format_output(avg) + b'\n', {}


if __name__ == '__main__':
    out, _ = main(sys.stdin.buffer.read(), {})
    sys.stdout.buffer.write(out)

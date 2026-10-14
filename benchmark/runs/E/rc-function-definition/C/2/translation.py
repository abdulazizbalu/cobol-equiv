def _accept_numeric(line: bytes, size: int) -> int:
    """Emulate MOVE of an alphanumeric ACCEPT value into an unsigned PIC 9(size)."""
    s = line
    dec_pt = ord('.')

    # Count the digits before the decimal point.
    count = 0
    for c in s:
        if c == dec_pt:
            break
        if 48 <= c <= 57:
            count += 1

    dst = [ord('0')] * size
    pos = 0
    i = 0
    n = len(s)
    if count < size:
        pos = size - count
    else:
        # Skip leading excess digits.
        excess = count - size
        while excess > 0 and i < n:
            if 48 <= s[i] <= 57:
                excess -= 1
            i += 1

    seen_dp = 0
    while i < n and pos < size:
        c = s[i]
        if 48 <= c <= 57:
            dst[pos] = c
            pos += 1
        elif c == dec_pt:
            seen_dp += 1
            # The field has no decimal places, so stop at the decimal point.
            break
        elif c in (32, 9, ord('+'), ord('-'), ord(',')):
            pass
        else:
            dst[pos] = ord('0') + (c & 0x0F)
            pos += 1
        i += 1

    val = 0
    for c in dst:
        d = c - 48
        if d < 0 or d > 9:
            d = d & 0x0F
            if d > 9:
                d = 0
        val = val * 10 + d
    return val


def main(stdin: bytes, input_files: dict) -> tuple:
    lines = stdin.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
    idx = 0

    x = 0
    y = 0

    if idx < len(lines):
        ln = lines[idx].rstrip(b'\r')
        idx += 1
        x = _accept_numeric(ln, 3)
    if idx < len(lines):
        ln = lines[idx].rstrip(b'\r')
        idx += 1
        y = _accept_numeric(ln, 3)

    z = (x * y) % 1000000000
    out = ("%09d" % z).encode() + b'\n'
    return out, {}

def _accept_numeric(line: bytes, int_digits: int = 9) -> int:
    # Emulates GnuCOBOL alphanumeric -> unsigned DISPLAY numeric move (PIC 9(9))
    s = line
    n = len(s)
    i = 0
    ws = b" \t\n\v\f\r"
    while i < n and s[i] in ws:
        i += 1
    if i < n and s[i] in b"+-":
        i += 1
    # count digits before decimal point
    count = 0
    p = i
    while p < n and s[p] != ord('.'):
        if 48 <= s[p] <= 57:
            count += 1
        p += 1
    out = [ord('0')] * int_digits
    pos = 0
    if count < int_digits:
        pos = int_digits - count
    else:
        while count > int_digits:
            count -= 1
            while i < n:
                c = s[i]
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
            # remaining positions are decimals; field has no decimals
            break
        elif not (c in ws or c == ord(',')):
            break
        i += 1
    return int(bytes(out).decode())


def main(stdin: bytes, input_files: dict) -> tuple:
    lines = stdin.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    idx = 0
    MAXD = 38
    average = 0  # scaled by 10^9
    amount = 0
    while True:
        if idx >= len(lines):
            break  # EOF: original would loop forever; stop here
        line = lines[idx]
        idx += 1
        current = _accept_numeric(line)
        if current == 99999:
            break
        amount = (amount + 1) % (10 ** 9)
        n = amount
        if n == 0:
            continue
        # term1 = AVERAGE*(AMOUNT-1)/AMOUNT
        prod = average * (n - 1)  # scale 9
        if prod == 0:
            t1v, t1s = 0, 0
        else:
            t1v, t1s = (prod * 10 ** MAXD) // n, 9 + MAXD
        # term2 = CURRENT/AMOUNT
        if current == 0:
            t2v, t2s = 0, 0
        else:
            t2v, t2s = (current * 10 ** MAXD) // n, MAXD
        s = max(t1s, t2s)
        total = t1v * 10 ** (s - t1s) + t2v * 10 ** (s - t2s)
        # store into 9(9)V9(9): truncate
        if s >= 9:
            val = total // 10 ** (s - 9)
        else:
            val = total * 10 ** (9 - s)
        average = val % (10 ** 18)
    ip = average // 10 ** 9
    fp = average % 10 ** 9
    istr = "%9d" % ip
    out = istr + "." + "%09d" % fp + "\n"
    return out.encode(), {}

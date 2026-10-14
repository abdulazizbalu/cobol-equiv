def _isdigit(c):
    return 48 <= c <= 57


def _isspace(c):
    return c in (32, 9, 10, 11, 12, 13)


def _move_alnum_to_num(src: bytes, size: int = 9, scale: int = 0) -> int:
    dst = bytearray(b'0' * size)
    s1 = 0
    e1 = len(src)
    while s1 < e1 and _isspace(src[s1]):
        s1 += 1
    if s1 != e1 and src[s1] in (43, 45):
        s1 += 1
    dec_pt = 46
    num_sep = 44
    count = 0
    p = s1
    while p < e1 and src[p] != dec_pt:
        if _isdigit(src[p]):
            count += 1
        p += 1
    isize = size - scale
    s2 = 0
    if count < isize:
        s2 = isize - count
    else:
        while count > isize:
            count -= 1
            while True:
                c = src[s1] if s1 < e1 else 0
                s1 += 1
                if _isdigit(c):
                    break
    cnt = 0
    while s1 < e1 and s2 < size:
        c = src[s1]
        if _isdigit(c):
            dst[s2] = c
            s2 += 1
        elif c == dec_pt:
            if cnt > 0:
                break
            cnt += 1
        elif not (_isspace(c) or c == num_sep):
            break
        s1 += 1
    return int(dst.decode('ascii'))


def main(stdin: bytes, input_files: dict) -> tuple:
    lines = stdin.split(b'\n')
    if stdin.endswith(b'\n'):
        lines = lines[:-1]
    idx = 0
    avg = 0  # scaled by 1e9
    amount = 0
    current = 0
    while True:
        if idx >= len(lines):
            break
        line = lines[idx]
        idx += 1
        current = _move_alnum_to_num(line)
        if current == 99999:
            break
        amount = (amount + 1) % 10**9
        n = amount
        if n == 0:
            continue
        t1 = (avg * (n - 1)) * 10**38 // n          # scale 47
        t2 = (current * 10**38 // n) * 10**9        # scale 47
        total = t1 + t2
        avg = (total // 10**38) % 10**18
    ip = avg // 10**9
    fp = avg % 10**9
    istr = str(ip).rjust(9)
    out = istr + '.' + str(fp).zfill(9) + '\n'
    return out.encode('ascii'), {}

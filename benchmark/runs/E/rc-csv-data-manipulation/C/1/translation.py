def _alnum_to_display(src: bytes, size: int) -> bytes:
    # Emulates GnuCOBOL cob_move_alphanum_to_display for an unsigned PIC 9(size)
    out = bytearray(b'0' * size)
    s1 = 0
    e1 = len(src)
    while s1 < e1 and chr(src[s1]) in ' \t\n\v\f\r':
        s1 += 1
    if s1 != e1 and src[s1] in (ord('+'), ord('-')):
        s1 += 1
    count = 0
    p = s1
    while p < e1 and src[p] != ord('.'):
        if 48 <= src[p] <= 57:
            count += 1
        p += 1
    s2 = 0
    if count < size:
        s2 = size - count
    else:
        while count > size:
            count -= 1
            while True:
                c = src[s1]
                s1 += 1
                if 48 <= c <= 57:
                    break
    dots = 0
    while s1 < e1 and s2 < size:
        c = src[s1]
        if 48 <= c <= 57:
            out[s2] = c
            s2 += 1
        elif c == ord('.'):
            if dots > 0:
                break
            dots += 1
        elif not (chr(c) in ' \t\n\v\f\r' or c == ord(',')):
            break
        s1 += 1
    return bytes(out)


def _trim(b: bytes) -> bytes:
    return b.strip(b' ')


def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get('csv.txt', b'')
    lines = data.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
    records = []
    for ln in lines:
        r = ln[:64]
        r = r + b' ' * (64 - len(r))
        records.append(r)

    out = bytearray()
    out_line = bytearray(b'\x00' * 80)
    csv_record = b'\x00' * 64
    cols = [b'00000'] * 5

    def string_into(parts):
        pos = 0
        for p in parts:
            for ch in p:
                if pos >= 80:
                    return
                out_line[pos] = ch
                pos += 1

    def write():
        out.extend(bytes(out_line).rstrip(b' '))
        out.extend(b'\n')

    idx = 0
    eof = False

    def read():
        nonlocal idx, eof, csv_record
        if idx < len(records):
            csv_record = records[idx]
            idx += 1
        else:
            eof = True

    read()
    # Build-Header
    string_into([_trim(csv_record), b',SUM'])
    write()
    out_line[:] = b' ' * 80

    while not eof:
        read()
        if not eof:
            parts = csv_record.split(b',')
            for i in range(min(5, len(parts))):
                cols[i] = _alnum_to_display(parts[i], 5)
            total = sum(int(c) for c in cols) % 10000
            s = str(total).rjust(4).encode()
            string_into([_trim(csv_record), b',', _trim(s)])
            write()
            out_line[:] = b' ' * 80

    return b'', {'new.csv.txt': bytes(out)}

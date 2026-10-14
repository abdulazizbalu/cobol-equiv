def _split_lines(data: bytes):
    lines = []
    i = 0
    n = len(data)
    while i < n:
        j = data.find(b"\n", i)
        if j < 0:
            lines.append(data[i:])
            break
        lines.append(data[i:j])
        i = j + 1
    return lines


def _fit(line: bytes, size: int) -> bytes:
    if len(line) >= size:
        return line[:size]
    return line + b" " * (size - len(line))


def _trim(b: bytes) -> bytes:
    return b.strip(b" ")


_SPACE = b" \t\n\v\f\r"


def _move_alnum_to_num(src: bytes, size: int) -> bytes:
    if len(src) == 0:
        return b"0" * size
    dst = bytearray(b"0" * size)
    s1 = 0
    e1 = len(src)
    while s1 < e1 and src[s1] in _SPACE:
        s1 += 1
    if s1 != e1 and src[s1] in b"+-":
        s1 += 1
    count = 0
    p = s1
    while p < e1 and src[p] != ord("."):
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
            dst[s2] = c
            s2 += 1
        elif c == ord("."):
            if dots > 0:
                break
            dots += 1
        elif not (c in _SPACE or c == ord(",")):
            break
        s1 += 1
    return bytes(dst)


def _string_into(buf: bytearray, parts):
    pos = 0
    for part in parts:
        for c in part:
            if pos >= len(buf):
                return
            buf[pos] = c
            pos += 1


def _write_ls(out: bytearray, rec: bytearray):
    out += bytes(rec).rstrip(b" ") + b"\n"


def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get("csv.txt", b"")
    lines = _split_lines(data)
    idx = 0
    out = bytearray()

    csv_record = b"\x00" * 64
    out_line = bytearray(b"\x00" * 80)
    eof = "F"
    cols = [b"00000"] * 5

    def read():
        nonlocal idx, csv_record, eof
        if idx < len(lines):
            csv_record = _fit(lines[idx], 64)
            idx += 1
        else:
            eof = "T"

    read()
    # Build-Header
    _string_into(out_line, [_trim(csv_record), b",SUM"])
    _write_ls(out, out_line)
    out_line = bytearray(b" " * 80)

    while eof != "T":
        read()
        if eof != "T":
            # UNSTRING
            rec = csv_record
            pos = 0
            for k in range(5):
                if pos >= len(rec):
                    break
                j = rec.find(b",", pos)
                if j < 0:
                    cols[k] = _move_alnum_to_num(rec[pos:], 5)
                    pos = len(rec)
                    break
                cols[k] = _move_alnum_to_num(rec[pos:j], 5)
                pos = j + 1
            total = sum(int(c) for c in cols) % 10000
            s = str(total).rjust(4).encode()
            _string_into(out_line, [_trim(csv_record), b",", _trim(s)])
            _write_ls(out, out_line)
            out_line = bytearray(b" " * 80)

    return b"", {"new.csv.txt": bytes(out)}

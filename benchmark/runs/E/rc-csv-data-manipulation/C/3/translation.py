def _read_lines(data: bytes):
    recs = []
    if not data:
        return recs
    parts = data.split(b"\n")
    if parts and parts[-1] == b"":
        parts.pop()
    for p in parts:
        r = p[:64]
        r = r + b" " * (64 - len(r))
        recs.append(r)
    return recs


def _trim(b: bytes) -> bytes:
    return b.strip(b" ")


_SPACES = b" \t\n\v\f\r"


def _move_alnum_to_num(src: bytes, size: int = 5) -> bytes:
    out = bytearray(b"0" * size)
    s1 = 0
    e1 = len(src)
    while s1 < e1 and src[s1] in _SPACES:
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
    dp = 0
    while s1 < e1 and s2 < size:
        c = src[s1]
        if 48 <= c <= 57:
            out[s2] = c
            s2 += 1
        elif c == ord("."):
            if dp > 0:
                break
            dp += 1
        elif not (c in _SPACES or c == ord(",")):
            break
        s1 += 1
    return bytes(out)


def _string_into(target: bytearray, pieces):
    pos = 0
    for piece in pieces:
        for c in piece:
            if pos >= len(target):
                return
            target[pos] = c
            pos += 1


def main(stdin: bytes, input_files: dict) -> tuple:
    recs = _read_lines(input_files.get("csv.txt", b""))
    idx = 0
    csv_record = b"\x00" * 64
    out_line = bytearray(b"\x00" * 80)
    out = bytearray()
    cols = [b"00000"] * 5
    eof = False

    def read():
        nonlocal idx, csv_record, eof
        if idx < len(recs):
            csv_record = recs[idx]
            idx += 1
        else:
            eof = True

    def write():
        out.extend(bytes(out_line).rstrip(b" "))
        out.extend(b"\n")

    read()
    # Build-Header
    _string_into(out_line, [_trim(csv_record), b",SUM"])
    write()
    out_line[:] = b" " * 80

    while not eof:
        read()
        if not eof:
            parts = csv_record.split(b",")
            for i in range(min(5, len(parts))):
                cols[i] = _move_alnum_to_num(parts[i])
            total = sum(int(c) for c in cols) % 10000
            s = str(total).rjust(4).encode()
            _string_into(out_line, [_trim(csv_record), b",", _trim(s)])
            write()
            out_line[:] = b" " * 80

    return b"", {"new.csv.txt": bytes(out)}

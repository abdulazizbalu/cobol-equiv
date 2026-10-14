def main(stdin: bytes, input_files: dict) -> tuple:
    REC = 170
    data = input_files.get('ACCTREC', b'')
    records = []
    pos = 0
    while pos < len(data):
        chunk = data[pos:pos + REC]
        if len(chunk) < REC:
            chunk = chunk + b' ' * (REC - len(chunk))
        records.append(chunk)
        pos += REC

    # Table of 45 items, default initialized: alphanumerics are spaces
    last_names = [b' ' * 20 for _ in range(45)]

    ri = 0
    eof = False

    def read():
        nonlocal ri, eof
        if ri < len(records):
            r = records[ri]
            ri += 1
            return r
        eof = True
        return None

    cur = read()
    tv = 1
    while not (tv == 45 or eof):
        last_names[tv - 1] = cur[18:38]
        nxt = read()
        if nxt is not None:
            cur = nxt
        tv += 1

    target = b'ROOSEVELT'.ljust(20, b' ')
    found = any(ln == target for ln in last_names)
    out = b'Roosevelt is found!\n' if found else b'Not Found\n'
    return out, {}

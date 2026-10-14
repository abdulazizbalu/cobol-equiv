def main(stdin: bytes, input_files: dict) -> tuple:
    REC = 170
    MAX_OCC = 45
    TABLE_MAX = 45

    data = input_files.get('ACCTREC', b'')

    # Split the file into fixed 170-byte records.
    records = []
    pos = 0
    n = len(data)
    while pos < n:
        chunk = data[pos:pos + REC]
        if len(chunk) < REC:
            chunk = chunk + b' ' * (REC - len(chunk))
        records.append(chunk)
        pos += REC

    # Table initialised: alphanumeric fields are spaces.
    keys = [b' ' * 8 for _ in range(MAX_OCC + 1)]  # 1-based

    rec_iter = iter(records)
    eof = False
    current = None

    def read_record():
        nonlocal eof, current
        try:
            current = next(rec_iter)
        except StopIteration:
            eof = True

    read_record()
    table_var = 1
    while not (table_var == TABLE_MAX or eof):
        keys[table_var] = current[:8]
        read_record()
        table_var += 1

    # SEARCH ALL, GnuCOBOL-style binary search.
    value = b'18011809'
    out = []
    head = 0
    tail = MAX_OCC + 1
    while True:
        if head >= tail - 1:
            out.append(b'Not Found\n')
            break
        idx = (head + tail) // 2
        k = keys[idx]
        if k == value:
            out.append(b'User with Acct No 18011809 is found!\n')
            break
        if k < value:
            head = idx
        else:
            tail = idx

    return b''.join(out), {}

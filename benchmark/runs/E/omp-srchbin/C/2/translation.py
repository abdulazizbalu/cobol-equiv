def main(stdin: bytes, input_files: dict) -> tuple:
    REC_LEN = 170
    OCCURS = 45
    data = input_files.get('ACCTREC', b'')

    # Split the file into fixed-length records.
    records = []
    pos = 0
    while pos < len(data):
        chunk = data[pos:pos + REC_LEN]
        if len(chunk) < REC_LEN:
            chunk = chunk + b' ' * (REC_LEN - len(chunk))
        records.append(chunk)
        pos += REC_LEN

    # Unfilled entries are initialised to spaces, so ACCT-NO is all spaces.
    acct_nos = [b' ' * 8 for _ in range(OCCURS + 1)]  # 1-based

    rec_iter = iter(records)
    eof = False
    current = b' ' * REC_LEN

    def read_record():
        nonlocal eof, current
        try:
            current = next(rec_iter)
        except StopIteration:
            eof = True

    read_record()
    table_var = 1
    while not (table_var == 45 or eof):
        acct_nos[table_var] = current[:8]
        read_record()
        table_var += 1

    # SEARCH ALL as a binary search, following GnuCOBOL's code generation.
    key = b'18011809'
    out = []
    head = 0
    tail = OCCURS + 1
    while True:
        if head >= tail - 1:
            out.append(b'Not Found\n')
            break
        idx = (head + tail) // 2
        v = acct_nos[idx]
        if v == key:
            out.append(b'User with Acct No 18011809 is found!\n')
            break
        if v < key:
            head = idx
        else:
            tail = idx

    return b''.join(out), {}

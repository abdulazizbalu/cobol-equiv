def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    RECLEN = 170
    data = input_files.get('ACCTREC', b'')

    # Split the file into fixed-length records; pad a short final record with spaces.
    records = []
    pos = 0
    while pos < len(data):
        rec = data[pos:pos + RECLEN]
        if len(rec) < RECLEN:
            rec = rec + b' ' * (RECLEN - len(rec))
        records.append(rec)
        pos += RECLEN

    # Table starts initialised: ACCT-NO fields are spaces.
    table_keys = [b' ' * 8 for _ in range(45)]

    # Load: the first READ comes before the loop. The loop runs while
    # TABLE-VAR != 45 and not at end of file, so at most 44 rows load.
    rec_iter = iter(records)

    def read():
        try:
            return next(rec_iter)
        except StopIteration:
            return None

    cur = read()
    eof = cur is None
    table_var = 1
    while not (table_var == 45 or eof):
        table_keys[table_var - 1] = cur[:8]
        cur = read()
        if cur is None:
            eof = True
        table_var += 1

    # SEARCH ALL: binary search over all 45 entries.
    value = b'18011809'
    lo, hi = 1, 45
    found = False
    while lo <= hi:
        idx = (lo + hi) // 2
        key = table_keys[idx - 1]
        if key == value:
            found = True
            break
        if key < value:
            lo = idx + 1
        else:
            hi = idx - 1

    if found:
        out = b'User with Acct No 18011809 is found!\n'
    else:
        out = b'Not Found\n'
    return out, {}

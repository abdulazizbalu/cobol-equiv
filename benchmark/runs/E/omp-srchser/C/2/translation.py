def main(stdin: bytes, input_files: dict) -> tuple:
    REC_LEN = 170
    TABLE_SIZE = 45
    TABLE_MAX = 45

    data = input_files.get('ACCTREC', b'')

    # Split the file into fixed-length records; pad a short final record with spaces
    records = []
    pos = 0
    while pos < len(data):
        chunk = data[pos:pos + REC_LEN]
        if len(chunk) < REC_LEN:
            chunk = chunk + b' ' * (REC_LEN - len(chunk))
        records.append(chunk)
        pos += REC_LEN

    # Initial table: LAST-NAME of every item is spaces
    last_names = [b' ' * 20 for _ in range(TABLE_SIZE)]

    rec_iter = iter(records)
    eof = False

    def read_record():
        nonlocal eof
        try:
            return next(rec_iter)
        except StopIteration:
            eof = True
            return None

    cur = read_record()
    table_var = 1
    while not (table_var == TABLE_MAX or eof):
        last_names[table_var - 1] = cur[18:38]
        cur = read_record()
        table_var += 1

    target = b'ROOSEVELT'.ljust(20, b' ')
    found = False
    for idx in range(TABLE_SIZE):
        if last_names[idx] == target:
            found = True
            break

    if found:
        out = b'Roosevelt is found!\n'
    else:
        out = b'Not Found\n'
    return out, {}

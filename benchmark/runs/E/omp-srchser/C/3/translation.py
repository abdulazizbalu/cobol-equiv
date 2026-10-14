def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
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

    # Initialize table: 45 items, alphanumeric spaces, packed zeros
    zero_packed = b'\x00\x00\x00\x00\x0c'
    init_item = b' ' * 8 + zero_packed + zero_packed + b' ' * (REC - 18)
    table = [init_item] * 45

    # Load: read first; loop TABLE-VAR from 1 until =45 or EOF
    ri = 0
    eof = False
    if ri < len(records):
        cur = records[ri]
        ri += 1
    else:
        eof = True
    tv = 1
    while not (tv == 45 or eof):
        table[tv - 1] = cur
        if ri < len(records):
            cur = records[ri]
            ri += 1
        else:
            eof = True
        tv += 1

    target = b'ROOSEVELT'.ljust(20, b' ')
    found = False
    for item in table:
        if item[18:38] == target:
            found = True
            break
    if found:
        out = b'Roosevelt is found!\n'
    else:
        out = b'Not Found\n'
    return out, {}

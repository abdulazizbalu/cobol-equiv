def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get('File.txt', b'')
    lines = data.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()

    counts = [0] * 26
    record = b' ' * 80

    def tally(rec):
        up = rec.upper()
        for i in range(26):
            c = up.count(bytes([65 + i]))
            counts[i] = (counts[i] + c) % 100000

    idx = 0
    eof = False
    while not eof:
        if idx < len(lines):
            rec = lines[idx][:80]
            record = rec + b' ' * (80 - len(rec))
            idx += 1
        else:
            eof = True
        tally(record)

    out = []
    out.append(b'Letter Frequency Distribution\n')
    out.append(b'-----------------------------\n')
    for i in range(13):
        a = chr(65 + i).encode()
        b = chr(65 + 13 + i).encode()
        out.append(a + b' : ' + ('%5d' % counts[i]).encode() + b'          '
                   + b + b' : ' + ('%5d' % counts[13 + i]).encode() + b'\n')
    return b''.join(out), {}

def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get("File.txt", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    counts = [0] * 26
    record = b" " * 80

    def tally(rec):
        up = bytes((c - 32) if 97 <= c <= 122 else c for c in rec)
        for i in range(26):
            n = up.count(bytes([65 + i]))
            counts[i] = (counts[i] + n) % 100000

    idx = 0
    eof = False
    while not eof:
        if idx < len(lines):
            line = lines[idx]
            idx += 1
            if len(line) >= 80:
                record = line[:80]
            else:
                record = line + b" " * (80 - len(line))
        else:
            eof = True
        tally(record)

    out = []
    out.append(b"Letter Frequency Distribution\n")
    out.append(b"-----------------------------\n")
    for i in range(13):
        l1 = bytes([65 + i])
        l2 = bytes([65 + 13 + i])
        c1 = str(counts[i]).rjust(5).encode()
        c2 = str(counts[13 + i]).rjust(5).encode()
        out.append(l1 + b" : " + c1 + b"          " + l2 + b" : " + c2 + b"\n")
    return b"".join(out), {}

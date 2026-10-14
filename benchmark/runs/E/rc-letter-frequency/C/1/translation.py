def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get("File.txt", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    counts = [0] * 26
    record = bytes(80)  # initial record area (zero-filled)

    def tally(rec):
        up = rec.upper()
        for i in range(26):
            c = 65 + i
            n = up.count(bytes([c]))
            if n:
                counts[i] = (counts[i] + n) % 100000

    idx = 0
    eof = False
    while not eof:
        if idx < len(lines):
            line = lines[idx]
            idx += 1
            rec = line[:80]
            rec = rec + b" " * (80 - len(rec))
            record = rec
        else:
            eof = True
        tally(record)

    def fmt(n):
        return str(n).rjust(5).encode()

    out = []
    out.append(b"Letter Frequency Distribution\n")
    out.append(b"-----------------------------\n")
    for i in range(13):
        l1 = bytes([65 + i])
        l2 = bytes([65 + 13 + i])
        out.append(l1 + b" : " + fmt(counts[i]) + b"          " +
                   l2 + b" : " + fmt(counts[13 + i]) + b"\n")
    return b"".join(out), {}

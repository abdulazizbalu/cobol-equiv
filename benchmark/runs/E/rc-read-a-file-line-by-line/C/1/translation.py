def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = []
    if "input.txt" not in input_files:
        out.append(b"The file could not be opened.\n")
        return b"".join(out), {}

    data = input_files["input.txt"]
    # Split into line-sequential records
    lines = []
    pos = 0
    n = len(data)
    while pos < n:
        idx = data.find(b"\n", pos)
        if idx == -1:
            lines.append(data[pos:])
            pos = n
        else:
            lines.append(data[pos:idx])
            pos = idx + 1

    record = b" " * 256
    status = 0
    line_count = 1
    li = 0
    while status != 10:
        if li < len(lines):
            rec = lines[li][:256]
            li += 1
            record = rec + b" " * (256 - len(rec))
            status = 0
        else:
            status = 10
        trimmed = record.strip(b" ")
        out.append(b"%06d: " % (line_count % 1000000) + trimmed + b"\n")
        line_count = (line_count + 1) % 1000000

    return b"".join(out), {}

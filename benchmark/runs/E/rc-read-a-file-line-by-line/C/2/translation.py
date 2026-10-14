def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = []
    if "input.txt" not in input_files:
        out.append(b"The file could not be opened.\n")
        return b"".join(out), {}

    data = input_files["input.txt"]
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    record = b" " * 256
    idx = 0
    line_count = 1
    eof = False
    while not eof:
        if idx < len(lines):
            content = lines[idx][:256]
            idx += 1
            record = content + b" " * (256 - len(content))
        else:
            eof = True
        trimmed = record.strip(b" ")
        out.append(b"%06d: " % (line_count % 1000000) + trimmed + b"\n")
        line_count = (line_count + 1) % 1000000

    return b"".join(out), {}

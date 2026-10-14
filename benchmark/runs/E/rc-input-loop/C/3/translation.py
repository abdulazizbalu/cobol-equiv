def main(stdin: bytes, input_files: dict) -> tuple:
    out = bytearray()
    data = stdin
    pos = 0
    n = len(data)
    while pos < n:
        nl = data.find(b"\n", pos)
        if nl == -1:
            line = data[pos:]
            pos = n
        else:
            line = data[pos:nl]
            pos = nl + 1
        rec = line[:80]
        rec = rec + b" " * (80 - len(rec))
        out += rec + b"\n"
    return bytes(out), {}

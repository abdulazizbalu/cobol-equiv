def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    data = input_files.get("input.txt", b"")
    size = 80
    out = bytearray()
    pos = 0
    n = len(data)
    while pos < n:
        rec = data[pos:pos + size]
        pos += size
        if len(rec) < size:
            rec = rec + b" " * (size - len(rec))
        out += rec
    return b"", {"output.txt": bytes(out)}

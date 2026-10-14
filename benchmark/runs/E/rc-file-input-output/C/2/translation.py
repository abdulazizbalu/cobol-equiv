def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    data = input_files.get("input.txt", b"")
    size = 80
    record = bytearray(b" " * size)
    out = bytearray()
    pos = 0
    n = len(data)
    while pos < n:
        chunk = data[pos:pos + size]
        pos += size
        record[:len(chunk)] = chunk
        out += bytes(record)
    return b"", {"output.txt": bytes(out)}

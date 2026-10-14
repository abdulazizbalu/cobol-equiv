def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    data = stdin
    out = bytearray()
    if not data:
        return b"", {}
    parts = data.split(b"\n")
    if data.endswith(b"\n"):
        parts = parts[:-1]
    for line in parts:
        rec = line[:80]
        rec = rec + b" " * (80 - len(rec))
        out += rec + b"\n"
    return bytes(out), {}

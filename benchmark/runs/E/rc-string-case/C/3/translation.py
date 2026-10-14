def _lower(b: bytes) -> bytes:
    return bytes((c + 32) if 65 <= c <= 90 else c for c in b)


def _upper(b: bytes) -> bytes:
    return bytes((c - 32) if 97 <= c <= 122 else c for c in b)


def main(stdin: bytes, input_files: dict) -> tuple:
    example = b" " * 9
    if stdin:
        nl = stdin.find(b"\n")
        line = stdin if nl < 0 else stdin[:nl]
        if line.endswith(b"\r"):
            line = line[:-1]
        example = (line[:9]).ljust(9, b" ")

    out = bytearray()
    out += b"Example: " + example + b"\n"
    out += b"Lower-case: " + _lower(example) + b"\n"
    out += b"Upper-case: " + _upper(example) + b"\n"
    out += b"Lower-case: " + _lower(example) + b"\n"
    out += b"Upper-case: " + _upper(example) + b"\n"
    return bytes(out), {}

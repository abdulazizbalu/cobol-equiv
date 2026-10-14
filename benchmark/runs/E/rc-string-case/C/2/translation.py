def main(stdin: bytes, input_files: dict) -> tuple:
    # ACCEPT example: read one line, then truncate or pad with spaces to PIC X(9)
    line = stdin.split(b"\n", 1)[0] if stdin else b""
    example = line[:9].ljust(9, b" ")

    lower_tbl = bytes.maketrans(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                                b"abcdefghijklmnopqrstuvwxyz")
    upper_tbl = bytes.maketrans(b"abcdefghijklmnopqrstuvwxyz",
                                b"ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    lower = example.translate(lower_tbl)
    upper = example.translate(upper_tbl)

    out = bytearray()
    out += b"Example: " + example + b"\n"
    out += b"Lower-case: " + lower + b"\n"
    out += b"Upper-case: " + upper + b"\n"
    out += b"Lower-case: " + lower + b"\n"
    out += b"Upper-case: " + upper + b"\n"
    return bytes(out), {}

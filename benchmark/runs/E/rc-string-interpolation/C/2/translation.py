def main(stdin: bytes, input_files: dict) -> tuple:
    # ACCEPT reads one line into PIC X(6): truncate or pad with spaces
    if stdin:
        nl = stdin.find(b"\n")
        line = stdin if nl < 0 else stdin[:nl]
        if line.endswith(b"\r"):
            line = line[:-1]
    else:
        line = b""
    extra = line[:6].ljust(6, b" ")

    # FUNCTION SUBSTITUTE replaces every "X" with the full 6-byte field
    result = b"Mary had a X lamb.".replace(b"X", extra)
    return result + b"\n", {}

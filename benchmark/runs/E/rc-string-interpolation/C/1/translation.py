def main(stdin: bytes, input_files: dict) -> tuple:
    # ACCEPT extra : read one line, fit into PIC X(6)
    extra = b" " * 6
    if stdin:
        nl = stdin.find(b"\n")
        line = stdin if nl < 0 else stdin[:nl]
        extra = (line[:6]).ljust(6, b" ")
    result = b"Mary had a X lamb.".replace(b"X", extra)
    return result + b"\n", {}

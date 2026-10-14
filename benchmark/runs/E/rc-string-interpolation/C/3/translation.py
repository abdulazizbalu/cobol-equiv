def main(stdin: bytes, input_files: dict) -> tuple:
    # ACCEPT extra: read one line
    if stdin:
        idx = stdin.find(b"\n")
        line = stdin if idx < 0 else stdin[:idx]
    else:
        line = b""
    extra = line[:6].ljust(6, b" ")

    # FUNCTION SUBSTITUTE("Mary had a X lamb.", "X", extra)
    src = b"Mary had a X lamb."
    result = src.replace(b"X", extra)

    out = result + b"\n"
    return out, {}

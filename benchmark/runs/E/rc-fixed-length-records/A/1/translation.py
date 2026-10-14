from cobol_equiv.runtime import Storage, Alnum  # noqa: F401  (runtime available; plain bytes suffice here)

RECLEN = 80


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()
    files: dict[str, bytes] = {}

    data = input_files.get("infile.dat")
    if data is None:
        # open input fails -> message to syserr, goback
        return bytes(out), files

    # open output outfile
    written = bytearray()

    pos = 0
    n = len(data)
    while pos + RECLEN <= n:
        rec = data[pos:pos + RECLEN]
        pos += RECLEN
        written += rec[::-1]

    files["outfile.dat"] = bytes(written)

    # reopen outfile for input and display each record trimmed trailing
    wpos = 0
    wn = len(written)
    while wpos + RECLEN <= wn:
        rec = bytes(written[wpos:wpos + RECLEN])
        wpos += RECLEN
        out += rec.rstrip(b" ") + b"\n"

    return bytes(out), files

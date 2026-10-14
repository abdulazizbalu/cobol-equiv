def main(stdin: bytes, input_files: dict) -> tuple:
    out = bytearray()
    files = {}

    data = input_files.get("infile.dat")
    if data is None:
        # open input failed: message goes to stderr, program ends
        return bytes(out), files

    reclen = 80
    out_records = []
    pos = 0
    n = len(data)
    while pos + reclen <= n:
        rec = data[pos:pos + reclen]
        pos += reclen
        out_records.append(rec[::-1])
    # A short trailing record would end the loop (non-'00' status).

    content = b"".join(out_records)
    files["outfile.dat"] = content

    for rec in out_records:
        out += rec.rstrip(b" ")
        out += b"\n"

    return bytes(out), files

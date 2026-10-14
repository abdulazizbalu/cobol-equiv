def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    RECLEN = 80
    data = input_files.get("infile.dat", b"")

    out_records = []
    pos = 0
    # READ loop: continue while status is '00' (full 80-byte records)
    while pos + RECLEN <= len(data):
        rec = data[pos:pos + RECLEN]
        pos += RECLEN
        out_records.append(rec[::-1])

    out_content = b"".join(out_records)

    stdout = bytearray()
    for rec in out_records:
        stdout += rec.rstrip(b" ") + b"\n"

    return bytes(stdout), {"outfile.dat": out_content}

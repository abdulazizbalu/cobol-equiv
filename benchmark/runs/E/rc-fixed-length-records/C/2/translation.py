def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    RL = 80
    if "infile.dat" not in input_files:
        # open input fails -> error to syserr, goback
        return b"", {}
    data = input_files["infile.dat"]

    out_records = []
    pos = 0
    n = len(data)
    while True:
        if pos >= n:
            break  # status 10
        chunk = data[pos:pos + RL]
        pos += RL
        if len(chunk) < RL:
            break  # short record -> status 04, not ok-input
        out_records.append(chunk[::-1])

    out_content = b"".join(out_records)

    stdout_parts = []
    for rec in out_records:
        stdout_parts.append(rec.rstrip(b" ") + b"\n")

    return b"".join(stdout_parts), {"outfile.dat": out_content}

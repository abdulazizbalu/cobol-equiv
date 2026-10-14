def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    RECLEN = 80
    data = input_files.get("input.txt", b"")
    out = bytearray()
    record = bytearray(b" " * RECLEN)
    pos = 0
    n = len(data)
    while pos < n:
        chunk = data[pos:pos + RECLEN]
        pos += RECLEN
        if len(chunk) == RECLEN:
            record[:] = chunk
        else:
            # Short final record: GnuCOBOL reports status 04 and treats the
            # read as successful; pad the rest of the record with spaces.
            record[:] = chunk + b" " * (RECLEN - len(chunk))
        out += record
    return b"", {"output.txt": bytes(out)}

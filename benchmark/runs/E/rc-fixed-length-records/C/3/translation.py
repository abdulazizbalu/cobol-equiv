def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    RECLEN = 80
    out = bytearray()
    files = {}

    if 'infile.dat' not in input_files:
        # open input fails (status 35); error goes to syserr; goback
        return bytes(out), files

    data = input_files['infile.dat']

    # Open output outfile (truncate)
    outdata = bytearray()

    pos = 0
    n = len(data)
    while pos + RECLEN <= n:
        rec = data[pos:pos + RECLEN]
        pos += RECLEN
        outdata += rec[::-1]
    # A partial trailing record (status not '00') ends the loop.

    files['outfile.dat'] = bytes(outdata)

    # Reopen outfile for input and display each record trimmed of trailing spaces
    pos = 0
    n = len(outdata)
    while pos + RECLEN <= n:
        rec = bytes(outdata[pos:pos + RECLEN])
        pos += RECLEN
        out += rec.rstrip(b' ') + b'\n'

    return bytes(out), files

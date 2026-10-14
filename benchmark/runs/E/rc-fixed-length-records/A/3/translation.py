from cobol_equiv.runtime import Storage, Alnum
from cobol_equiv.runtime.files import RecordSequentialReader, RecordSequentialWriter

REC = 80


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()
    data = input_files.get("infile.dat", b"")

    in_rec = Storage("INFILE", [Alnum("INPUT-TEXT", "X(80)")])
    out_rec = Storage("OUTFILE", [Alnum("OUTPUT-TEXT", "X(80)")])

    # Only full records are processed; a short trailing record ends the loop
    # (non-'00' status).
    n_full = len(data) // REC
    reader = RecordSequentialReader(data[: n_full * REC], REC)
    writer = RecordSequentialWriter()

    while True:
        r = reader.read(in_rec["INPUT-TEXT"])
        if r is None:
            break
        rev = bytes(in_rec["INPUT-TEXT"].raw)[::-1]
        out_rec["OUTPUT-TEXT"].set_raw(rev)
        writer.write(out_rec["OUTPUT-TEXT"])

    content = writer.getvalue()

    # Re-read output file and display trimmed (trailing spaces) records
    reader2 = RecordSequentialReader(content, REC)
    while True:
        r = reader2.read(out_rec["OUTPUT-TEXT"])
        if r is None:
            break
        text = bytes(out_rec["OUTPUT-TEXT"].raw).rstrip(b" ")
        out += text + b"\n"

    return bytes(out), {"outfile.dat": content}

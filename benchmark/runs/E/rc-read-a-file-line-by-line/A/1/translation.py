from cobol_equiv.runtime import Storage, Alnum, Num
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()
    if "input.txt" not in input_files:
        out += b"The file could not be opened.\n"
        return bytes(out), {}

    rec = Storage("FD", [Alnum("INPUT-RECORD", "X(256)")], area=bytearray(256))
    record = rec["INPUT-RECORD"]
    reader = LineSequentialReader(input_files["input.txt"], 256)

    line_count = 1
    eof = False
    while not eof:
        r = reader.read(record)
        if r is None:
            eof = True
        data = record.raw.strip(b" ")
        out += b"%06d: " % (line_count % 1000000) + data + b"\n"
        line_count += 1

    return bytes(out), {}

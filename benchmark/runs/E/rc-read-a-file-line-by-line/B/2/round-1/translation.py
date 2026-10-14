from cobol_equiv.runtime import Storage, Alnum, Num
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()
    rec = Storage("FD", [Alnum("INPUT-RECORD", "X(256)")])
    record = rec["INPUT-RECORD"]
    record.set_raw(b"\x00" * 256)

    if "input.txt" not in input_files:
        out += b"The file could not be opened.\n"
        return bytes(out), {}

    reader = LineSequentialReader(input_files["input.txt"], 256)
    line_count = 1
    eof = False
    while not eof:
        data = reader.read(record)
        if data is None:
            eof = True
        lc = line_count % 1000000
        text = record.raw.strip(b" ")
        out += b"%06d" % lc + b": " + text + b"\n"
        line_count += 1

    return bytes(out), {}

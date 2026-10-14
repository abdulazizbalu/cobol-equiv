"""Reference translation of the Rosetta Code "Read a file line by line" solution
read-a-file-line-by-line.cob."""

from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict) -> tuple:
    reader = LineSequentialReader(input_files["input.txt"], 256)
    record = bytes(256)  # FD record area starts as binary zeros
    out = bytearray()
    count = 1
    eof = False
    while not eof:
        rec = reader.read()
        if rec is None:
            eof = True  # the DISPLAY below still runs on the unchanged record area
        else:
            record = rec
        out += b"%06d: " % (count % 1000000) + record.strip(b" ") + b"\n"
        count += 1
    return bytes(out), {}

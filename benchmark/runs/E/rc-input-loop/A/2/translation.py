from cobol_equiv.runtime import Storage, Alnum, Num, display_line
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    rec = Storage("IN-STREAM", [Alnum("STREAM-LINE", "X(80)")])
    ws = Storage("WS", [Num("IN-STREAM-STATUS", "99")])

    out = bytearray()
    reader = LineSequentialReader(stdin, 80)

    while True:
        r = reader.read(rec["STREAM-LINE"])
        if r is None:
            break
        out += display_line(rec["STREAM-LINE"])

    return bytes(out), {}

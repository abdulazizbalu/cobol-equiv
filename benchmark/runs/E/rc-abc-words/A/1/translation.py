from cobol_equiv.runtime import Storage, Alnum, display_line
from cobol_equiv.runtime.files import LineSequentialReader


def _count_before(data: bytes, ch: bytes) -> int:
    idx = data.find(ch)
    if idx < 0:
        return len(data)
    return idx


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    rec = Storage("DICT", [Alnum("WORD", "X(32)")])
    word = rec["WORD"]
    reader = LineSequentialReader(input_files.get("unixdict.txt", b""), 32)
    out = bytearray()

    while True:
        r = reader.read(word)
        if r is None:
            break
        data = word.raw
        a = _count_before(data, b"a") % 100
        b = _count_before(data, b"b") % 100
        c = _count_before(data, b"c") % 100
        x = _count_before(data, b" ") % 100
        if a < b and b < c and c < x:
            out += display_line(word)

    return bytes(out), {}

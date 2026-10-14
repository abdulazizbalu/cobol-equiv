from cobol_equiv.runtime import Storage, Alnum, display_line
from cobol_equiv.runtime.files import LineSequentialReader


def _count_before(raw: bytes, ch: bytes) -> int:
    idx = raw.find(ch)
    if idx < 0:
        return len(raw)
    return idx


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()
    fd = Storage("DICT", [Alnum("WORD", "X(32)")])
    word = fd["WORD"]
    reader = LineSequentialReader(input_files.get("unixdict.txt", b""), 32)

    while True:
        rec = reader.read(word)
        if rec is None:
            break
        raw = word.raw
        a = _count_before(raw, b"a") % 100
        b = _count_before(raw, b"b") % 100
        c = _count_before(raw, b"c") % 100
        x = _count_before(raw, b" ") % 100
        if a < b and b < c and c < x:
            out += display_line(word)

    return bytes(out), {}

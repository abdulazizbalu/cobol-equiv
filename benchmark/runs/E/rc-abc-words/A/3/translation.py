from cobol_equiv.runtime import (
    Storage, Num, Alnum, move, ZEROS, Phrase, inspect_tallying, display_line,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    rec = Storage("DICT-REC", [Alnum("WORD", "X(32)")])
    ws = Storage("WS", [
        Num("A", "99"),
        Num("B", "99"),
        Num("C", "99"),
        Num("X", "99"),
    ])
    word = rec["WORD"]
    a, b, c, x = ws["A"], ws["B"], ws["C"], ws["X"]

    out = bytearray()
    reader = LineSequentialReader(input_files.get("unixdict.txt", b""), 32)

    while True:
        r = reader.read(word)
        if r is None:
            break
        move(ZEROS, a, b, c, x)
        inspect_tallying(word, [Phrase("CHARACTERS", counter=a, before="a")])
        inspect_tallying(word, [Phrase("CHARACTERS", counter=b, before="b")])
        inspect_tallying(word, [Phrase("CHARACTERS", counter=c, before="c")])
        inspect_tallying(word, [Phrase("CHARACTERS", counter=x, before=" ")])
        if a.value < b.value and b.value < c.value and c.value < x.value:
            out += display_line(word)

    return bytes(out), {}

"""Reference translation of the Rosetta Code "ABC words" solution abc-words.cob."""

from cobol_equiv.runtime.files import LineSequentialReader


def _before(word: bytes, ch: bytes) -> int:
    """INSPECT word TALLYING n FOR CHARACTERS BEFORE INITIAL ch (n from 0)."""
    i = word.find(ch)
    return len(word) if i < 0 else i


def main(stdin: bytes, input_files: dict) -> tuple:
    reader = LineSequentialReader(input_files["unixdict.txt"], 32)
    out = bytearray()
    while True:
        word = reader.read()
        if word is None:
            break
        a, b, c, x = (_before(word, ch) for ch in (b"a", b"b", b"c", b" "))
        if a < b < c < x:
            out += word + b"\n"
    return bytes(out), {}

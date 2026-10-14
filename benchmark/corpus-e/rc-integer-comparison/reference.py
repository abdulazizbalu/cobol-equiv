"""Reference translation of the Rosetta Code "Integer comparison" solution integer-comparison.cob."""

from cobol_equiv.runtime import Num, Stdin, Storage, display_line


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = Storage("WS", [Num("A", "9(10)"), Num("B", "9(10)")])
    inp = Stdin(stdin)
    out = bytearray(b"First number: ")
    inp.accept(ws["A"])
    out += b"Second number: "
    inp.accept(ws["B"])
    a, b = ws["A"].value, ws["B"].value
    if a < b:
        out += display_line(ws["A"], " is less than ", ws["B"])
    elif a == b:
        out += display_line(ws["A"], " is equal to ", ws["B"])
    else:
        out += display_line(ws["A"], " is larger than ", ws["B"])
    return bytes(out), {}

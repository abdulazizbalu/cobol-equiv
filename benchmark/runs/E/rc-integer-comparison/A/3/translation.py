from cobol_equiv.runtime import (
    Storage, Num, Stdin, display_bytes, display_line, dec,
)


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Num("A", "9(10)"),
        Num("B", "9(10)"),
    ])
    a = ws["A"]
    b = ws["B"]
    inp = Stdin(stdin)
    out = bytearray()

    out += display_bytes("First number: ")
    inp.accept(a)
    out += display_bytes("Second number: ")
    inp.accept(b)

    da = dec(a)
    db = dec(b)
    if da < db:
        out += display_line(a, " is less than ", b)
    elif da == db:
        out += display_line(a, " is equal to ", b)
    elif da > db:
        out += display_line(a, " is larger than ", b)

    return bytes(out), {}

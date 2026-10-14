from cobol_equiv.runtime import Storage, Num, add_giving, display_line, Stdin


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Num("A", "S9(5)"),
        Num("B", "S9(5)"),
        Num("A-B-SUM", "S9(5)"),
    ])
    inp = Stdin(stdin)
    out = bytearray()

    inp.accept(ws["A"])
    inp.accept(ws["B"])

    add_giving([ws["A"], ws["B"]], ws["A-B-SUM"])

    out += display_line(ws["A-B-SUM"])

    return bytes(out), {}

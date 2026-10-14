from cobol_equiv.runtime import Storage, Num, add, display_line, Stdin


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Num("NUM-STR", "9(5)"),
    ])
    inp = Stdin(stdin)
    out = bytearray()

    inp.accept(ws["NUM-STR"])
    out += display_line(ws["NUM-STR"])
    add(1, ws["NUM-STR"])
    out += display_line(ws["NUM-STR"])

    return bytes(out), {}

from cobol_equiv.runtime import Storage, Group, Num, Stdin, display_line


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Group("WS-EXAMPLE", [
            Num("X", "9(5)V9(3)"),
        ]),
    ])
    inp = Stdin(stdin)
    out = bytearray()
    inp.accept(ws["X"])
    out += display_line(ws["X"])
    return bytes(out), {}

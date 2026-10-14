from cobol_equiv.runtime import Storage, Num, Stdin, add, display_line


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Num("NUM-STR", "9(5)"),
    ])
    inp = Stdin(stdin)
    out = bytearray()

    num = ws["NUM-STR"]
    inp.accept(num)
    out += display_line(num)
    add(1, num)
    out += display_line(num)

    return bytes(out), {}

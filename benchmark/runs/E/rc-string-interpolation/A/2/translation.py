from cobol_equiv.runtime import Storage, Alnum, Stdin, display_line


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Alnum("EXTRA", "X(6)"),
    ])
    inp = Stdin(stdin)
    inp.accept(ws["EXTRA"])
    result = b"Mary had a X lamb.".replace(b"X", ws["EXTRA"].raw)
    out = display_line(result)
    return out, {}

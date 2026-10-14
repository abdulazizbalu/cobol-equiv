from cobol_equiv.runtime import Storage, Alnum, Stdin


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Alnum("EXTRA", "X(6)"),
    ])
    inp = Stdin(stdin)
    inp.accept(ws["EXTRA"])

    literal = b"Mary had a X lamb."
    result = literal.replace(b"X", ws["EXTRA"].raw)

    out = bytearray()
    out += result + b"\n"
    return bytes(out), {}

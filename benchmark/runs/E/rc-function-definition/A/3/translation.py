from cobol_equiv.runtime import Storage, Num, Stdin, multiply_giving, display_line


def _my_multiply(x, y):
    # FUNCTION myMultiply: LINKAGE x, y, RETURNING z
    ls = Storage("LS", [
        Num("Z", "9(9)"),
    ])
    z = ls["Z"]
    multiply_giving(x, y, z)
    return z


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Num("X", "9(3)"),
        Num("Y", "9(3)"),
    ])
    inp = Stdin(stdin)
    out = bytearray()

    inp.accept(ws["X"])
    inp.accept(ws["Y"])
    z = _my_multiply(ws["X"], ws["Y"])
    out += display_line(z)

    return bytes(out), {}

from cobol_equiv.runtime import (
    Storage, Num, Alnum, move, divide_remainder, string, display_line, Stdin,
)


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Alnum("BINARY-NUMBER", "X(21)"),
        Alnum("STR", "X(21)"),
        Alnum("BINARY-DIGIT", "X"),
        Num("DIGIT", "9"),
        Num("N", "9(7)"),
        Alnum("NSTR", "X(7)"),
    ])
    out = bytearray()
    inp = Stdin(stdin)

    inp.accept(ws["NSTR"])
    move(ws["NSTR"], ws["N"])
    while int(ws["N"]) != 0:
        divide_remainder(ws["N"], 2, ws["N"], ws["DIGIT"])
        move(ws["DIGIT"], ws["BINARY-DIGIT"])
        string([(ws["BINARY-DIGIT"], None),
                (ws["BINARY-NUMBER"], " ")],
               ws["STR"])
        move(ws["STR"], ws["BINARY-NUMBER"])
    out += display_line(ws["BINARY-NUMBER"])
    return bytes(out), {}

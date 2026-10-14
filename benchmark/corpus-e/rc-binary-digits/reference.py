"""Reference translation of the Rosetta Code "Binary digits" solution binary-digits-1.cob."""

from cobol_equiv.runtime import Alnum, Num, Stdin, Storage, display_line, divide_remainder, move, string


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = Storage("WS", [Alnum("BINARY_NUMBER", "X(21)"), Alnum("STR", "X(21)"),
                        Alnum("BINARY_DIGIT", "X"), Num("DIGIT", "9"), Num("N", "9(7)"),
                        Alnum("NSTR", "X(7)")])
    Stdin(stdin).accept(ws["NSTR"])
    move(ws["NSTR"], ws["N"])
    while ws["N"].value != 0:
        divide_remainder(ws["N"], 2, ws["N"], ws["DIGIT"])
        move(ws["DIGIT"], ws["BINARY_DIGIT"])
        string([(ws["BINARY_DIGIT"], None), (ws["BINARY_NUMBER"], " ")], ws["STR"])
        move(ws["STR"], ws["BINARY_NUMBER"])
    return display_line(ws["BINARY_NUMBER"]), {}

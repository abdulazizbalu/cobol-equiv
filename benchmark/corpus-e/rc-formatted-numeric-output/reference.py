"""Reference translation of the Rosetta Code "Formatted numeric output" solution
formatted-numeric-output.cob (adapted: ACCEPT X)."""

from cobol_equiv.runtime import Num, Stdin, Storage, display_line


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = Storage("WS", [Num("X", "9(5)V9(3)")])
    Stdin(stdin).accept(ws["X"])
    return display_line(ws["X"]), {}

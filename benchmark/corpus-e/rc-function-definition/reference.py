"""Reference translation of the Rosetta Code "Function definition" solution
function-definition-2.cob (adapted: ACCEPT x, ACCEPT y)."""

from cobol_equiv.runtime import Num, Stdin, Storage, display_line, multiply_giving


def my_multiply(x, y):
    ls = Storage("LS", [Num("Z", "9(9)")])
    multiply_giving(x, y, ls["Z"])
    return ls["Z"]


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = Storage("WS", [Num("X", "9(3)"), Num("Y", "9(3)")])
    inp = Stdin(stdin)
    inp.accept(ws["X"])
    inp.accept(ws["Y"])
    return display_line(my_multiply(ws["X"], ws["Y"])), {}

"""Reference translation of the Rosetta Code "A+B" solution a+b-1.cob."""

from cobol_equiv.runtime import Stdin
from cobol_equiv.runtime import Num, Storage, add_giving, display_line


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = Storage("WS", [Num("A", "S9(5)"), Num("B", "S9(5)"), Num("A-B-SUM", "S9(5)")])
    inp = Stdin(stdin)
    inp.accept(ws["A"])
    inp.accept(ws["B"])
    add_giving([ws["A"], ws["B"]], ws["A-B-SUM"])
    return display_line(ws["A-B-SUM"]), {}

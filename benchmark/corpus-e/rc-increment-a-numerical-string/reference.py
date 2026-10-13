"""Reference translation of the Rosetta Code "Increment a numerical string" solution
increment-a-numerical-string-2.cob (adapted: ACCEPT num-str)."""

from cobol_equiv.runtime import Num, Stdin, Storage, add, display_line


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = Storage("WS", [Num("NUM-STR", "9(5)")])
    Stdin(stdin).accept(ws["NUM-STR"])
    out = display_line(ws["NUM-STR"])
    add(1, ws["NUM-STR"])
    return out + display_line(ws["NUM-STR"]), {}

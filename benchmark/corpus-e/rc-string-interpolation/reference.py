"""Reference translation of the Rosetta Code "String interpolation (included)" solution
string-interpolation-included-.cob (adapted: ACCEPT extra)."""

from cobol_equiv.runtime import Alnum, Stdin, Storage


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = Storage("WS", [Alnum("EXTRA", "X(6)")])
    Stdin(stdin).accept(ws["EXTRA"])
    return b"Mary had a X lamb.".replace(b"X", ws["EXTRA"].raw) + b"\n", {}

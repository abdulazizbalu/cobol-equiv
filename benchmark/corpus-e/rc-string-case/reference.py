"""Reference translation of the Rosetta Code "String case" solution string-case-1.cob
(adapted: ACCEPT example)."""

from cobol_equiv.runtime import Alnum, Stdin, Storage, inspect_converting, move


def _lower(b: bytes) -> bytes:
    return bytes(c + 32 if 0x41 <= c <= 0x5A else c for c in b)


def _upper(b: bytes) -> bytes:
    return bytes(c - 32 if 0x61 <= c <= 0x7A else c for c in b)


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = Storage("WS", [Alnum("EXAMPLE", "X(9)"), Alnum("RESULT", "X(9)")])
    Stdin(stdin).accept(ws["EXAMPLE"])
    ex = ws["EXAMPLE"].raw
    out = bytearray()
    out += b"Example: " + ex + b"\n"
    out += b"Lower-case: " + _lower(ex) + b"\n"
    out += b"Upper-case: " + _upper(ex) + b"\n"
    move(ws["EXAMPLE"], ws["RESULT"])
    inspect_converting(ws["RESULT"], "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")
    out += b"Lower-case: " + ws["RESULT"].raw + b"\n"
    move(ws["EXAMPLE"], ws["RESULT"])
    inspect_converting(ws["RESULT"], "abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    out += b"Upper-case: " + ws["RESULT"].raw + b"\n"
    return bytes(out), {}

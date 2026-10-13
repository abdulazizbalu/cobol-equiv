"""Reference translation of the Rosetta Code "Fibonacci sequence" solution
fibonacci-sequence-1.cob."""

from cobol_equiv.runtime import (Alnum, Edited, Num, Stdin, Storage, compute, dec, display_line,
                                 move, subtract, unstring)


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = Storage("WS", [
        Num("FIBONACCI-NUMBER", "9(36)", value=0), Num("FIB-ONE", "9(36)", value=0),
        Num("FIB-TWO", "9(36)", value=1), Num("DESIRED-COUNT", "9(4)"),
        Edited("INTERM-RESULT", "Z(35)9"), Alnum("FORMATTED-RESULT", "X(36)"),
        Alnum("FORMATTED-SPACE", "X(35)"),
    ])
    out = bytearray(b"What place of the Fibonacci Sequence would you like (<173)? ")
    Stdin(stdin).accept(ws["DESIRED-COUNT"])

    def show():
        nonlocal out
        move(ws["FIBONACCI-NUMBER"], ws["INTERM-RESULT"])
        move(ws["INTERM-RESULT"], ws["FORMATTED-RESULT"])
        unstring(ws["FORMATTED-RESULT"], [(" ", True)], [ws["FORMATTED-SPACE"], ws["FORMATTED-RESULT"]])
        out += display_line(ws["FORMATTED-RESULT"])

    if ws["DESIRED-COUNT"].value < 1:
        return bytes(out), {}
    if ws["DESIRED-COUNT"].value < 2:
        show()
        return bytes(out), {}
    subtract(1, ws["DESIRED-COUNT"])
    show()
    while ws["DESIRED-COUNT"].value != 0:
        compute(ws["FIBONACCI-NUMBER"], dec(ws["FIB-ONE"]) + dec(ws["FIB-TWO"]))
        move(ws["FIB-TWO"], ws["FIB-ONE"])
        move(ws["FIBONACCI-NUMBER"], ws["FIB-TWO"])
        subtract(1, ws["DESIRED-COUNT"])
        show()
    return bytes(out), {}

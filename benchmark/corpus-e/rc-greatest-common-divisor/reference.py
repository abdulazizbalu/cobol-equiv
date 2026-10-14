"""Reference translation of the Rosetta Code "Greatest common divisor" solution
greatest-common-divisor.cob."""

from cobol_equiv.runtime import Num, Stdin, Storage, display_line, divide_remainder, move


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = Storage("WS", [Num("A", "9(10)", value=0), Num("B", "9(10)", value=0),
                        Num("TEMP", "9(10)", value=0)])
    out = bytearray(b"Enter first number, max 10 digits.\n")
    inp = Stdin(stdin)
    inp.accept(ws["A"])
    out += b"Enter second number, max 10 digits.\n"
    inp.accept(ws["B"])
    if ws["A"].value < ws["B"].value:
        move(ws["B"], ws["TEMP"])
        move(ws["A"], ws["B"])
        move(ws["TEMP"], ws["B"])
    while ws["B"].value != 0:
        move(ws["A"], ws["TEMP"])
        move(ws["B"], ws["A"])
        divide_remainder(ws["TEMP"], ws["B"], ws["TEMP"], ws["B"])
    out += display_line("The gcd is ", ws["A"])
    return bytes(out), {}

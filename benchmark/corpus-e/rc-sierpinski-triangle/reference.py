"""Reference translation of the Rosetta Code "Sierpinski triangle" solution
sierpinski-triangle.cob (adapted: accept n)."""

from cobol_equiv.runtime import (Num, Stdin, Storage, compute, dec, divide_remainder, multiply_giving,
                                 subtract, subtract_giving)


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = Storage("WS", [Num("N", "99"), Num("I", "999"), Num("K", "999"), Num("M", "999"),
                        Num("C", "9(18)"), Num("I-LIMIT", "999"), Num("Q", "9(18)"), Num("R", "9")])
    Stdin(stdin).accept(ws["N"])
    multiply_giving(ws["N"], 4, ws["I-LIMIT"])
    subtract(1, ws["I-LIMIT"])
    out = bytearray()
    compute(ws["I"], 0)
    while not ws["I"].value > ws["I-LIMIT"].value:
        subtract_giving([ws["I"]], ws["I-LIMIT"], ws["M"])
        multiply_giving(ws["M"], 2, ws["M"])
        out += b" " * int(ws["M"].value)
        compute(ws["C"], 1)
        compute(ws["K"], 0)
        while not ws["K"].value > ws["I"].value:
            divide_remainder(ws["C"], 2, ws["Q"], ws["R"])
            out += b"  * " if ws["R"].value == 0 else b"    "
            compute(ws["C"], dec(ws["C"]) * (dec(ws["I"]) - dec(ws["K"])) / (dec(ws["K"]) + 1))
            compute(ws["K"], dec(ws["K"]) + 1)
        out += b" \n"  # DISPLAY '' prints one space
        compute(ws["I"], dec(ws["I"]) + 1)
    return bytes(out), {}

"""Reference translation of the Rosetta Code "Soloway's recurring rainfall" solution
soloways-recurring-rainfall.cob."""

from cobol_equiv.runtime import Edited, Num, Stdin, Storage, add, compute, dec, display_line, move


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = Storage("WS", [Num("AVERAGE", "9(9)V9(9)", value=0), Num("AMOUNT", "9(9)", value=0),
                        Num("CURRENT", "9(9)"), Edited("OUTPUT-VAL", "Z(8)9.9(9)")])
    inp = Stdin(stdin)
    while True:
        inp.accept(ws["CURRENT"])
        if ws["CURRENT"].value == 99999:
            break
        add(1, ws["AMOUNT"])
        compute(ws["AVERAGE"], dec(ws["AVERAGE"]) * (dec(ws["AMOUNT"]) - 1) / dec(ws["AMOUNT"])
                + dec(ws["CURRENT"]) / dec(ws["AMOUNT"]))
    move(ws["AVERAGE"], ws["OUTPUT-VAL"])
    return display_line(ws["OUTPUT-VAL"]), {}

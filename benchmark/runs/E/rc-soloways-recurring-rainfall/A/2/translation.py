from cobol_equiv.runtime import (
    Storage, Num, Edited, move, add, compute, dec, display_line, Stdin,
)


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Num("AVERAGE", "9(9)V9(9)", value=0),
        Num("AMOUNT", "9(9)", value=0),
        Num("CURRENT", "9(9)"),
        Edited("OUTPUT-VAL", "Z(8)9.9(9)"),
    ])
    inp = Stdin(stdin)
    out = bytearray()

    average = ws["AVERAGE"]
    amount = ws["AMOUNT"]
    current = ws["CURRENT"]
    output_val = ws["OUTPUT-VAL"]

    while True:
        inp.accept(current)
        if dec(current) == dec(99999):
            break
        add(1, amount)
        compute(
            average,
            dec(average) * (dec(amount) - dec(1)) / dec(amount)
            + dec(current) / dec(amount),
        )

    move(average, output_val)
    out += display_line(output_val)
    return bytes(out), {}

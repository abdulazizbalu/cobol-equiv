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

    # Guard against an endless loop when input never contains the sentinel.
    max_iter = stdin.count(b"\n") + 1000
    it = 0
    while True:
        inp.accept(current)
        if int(current) == 99999:
            break
        add(1, amount)
        compute(
            average,
            dec(average) * (dec(amount) - dec(1)) / dec(amount)
            + dec(current) / dec(amount),
        )
        it += 1
        if it > max_iter:
            raise RuntimeError("program does not terminate")

    move(average, ws["OUTPUT-VAL"])
    out += display_line(ws["OUTPUT-VAL"])
    return bytes(out), {}

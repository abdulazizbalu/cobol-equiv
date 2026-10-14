from cobol_equiv.runtime import (
    Storage, Num, Stdin, move, divide_remainder, display_line, dec,
)


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Num("A", "9(10)", value=0),
        Num("B", "9(10)", value=0),
        Num("TEMP", "9(10)", value=0),
    ])
    A = ws["A"]
    B = ws["B"]
    TEMP = ws["TEMP"]
    inp = Stdin(stdin)
    out = bytearray()

    out += display_line("Enter first number, max 10 digits.")
    inp.accept(A)
    out += display_line("Enter second number, max 10 digits.")
    inp.accept(B)

    if dec(A) < dec(B):
        move(B, TEMP)
        move(A, B)
        move(TEMP, B)

    while not (dec(B) == dec(0)):
        move(A, TEMP)
        move(B, A)
        dividend = dec(TEMP).to_decimal()
        divisor = dec(B).to_decimal()
        divide_remainder(dividend, divisor, TEMP, B)

    out += display_line("The gcd is ", A)
    return bytes(out), {}

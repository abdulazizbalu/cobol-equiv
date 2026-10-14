from decimal import Decimal

from cobol_equiv.runtime import (
    Storage, Num, Stdin, move, divide_remainder, display_line,
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

    if A.value < B.value:
        move(B, TEMP)
        move(A, B)
        move(TEMP, B)

    while not (B.value == Decimal(0)):
        move(A, TEMP)
        move(B, A)
        dividend = TEMP.value
        divisor = B.value
        divide_remainder(dividend, divisor, TEMP, B)

    out += display_line("The gcd is ", A)
    return bytes(out), {}

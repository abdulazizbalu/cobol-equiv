from cobol_equiv.runtime import (
    Storage,
    Num,
    ZEROS,
    move,
    divide_remainder,
    dec,
    display_line,
    Stdin,
)


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Num("A", "9(10)", value=ZEROS),
        Num("B", "9(10)", value=ZEROS),
        Num("TEMP", "9(10)", value=ZEROS),
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

    while B.value != 0:
        move(A, TEMP)
        move(B, A)
        divide_remainder(dec(TEMP), dec(B), TEMP, B)

    out += display_line("The gcd is ", A)
    return bytes(out), {}

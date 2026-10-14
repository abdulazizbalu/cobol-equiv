from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, move, initialize, display_line, Stdin, refmod,
)

_TABLE = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Num("WS-NUMBER", "9(4)", value=0),
        Num("WS-SAVE-NUMBER", "9(4)"),
        Num("OCX", "99"),
        Group("WS-ROMAN", [Alnum("WS-ROMAN-CH", "X(1)", occurs=16)]),
    ])
    inp = Stdin(stdin)
    out = bytearray()
    num = ws["WS-NUMBER"]

    inp.accept(num)
    while num.value != 0:
        move(num, ws["WS-SAVE-NUMBER"])
        if 0 < num.value < 4000:
            initialize(ws["WS-ROMAN"])
            n = int(num.value)
            ocx = 0
            for div, chars in _TABLE:
                if n == 0:
                    break
                while n >= div:
                    for c in chars:
                        ocx += 1
                        move(c, ws.f("WS-ROMAN-CH", ocx))
                    n -= div
            move(n, num)
            move(ocx, ws["OCX"])
            out += display_line("inp=", ws["WS-SAVE-NUMBER"], " roman=", ws["WS-ROMAN"])
        else:
            out += display_line("inp=", ws["WS-SAVE-NUMBER"], " invalid")
        inp.accept(num)

    return bytes(out), {}

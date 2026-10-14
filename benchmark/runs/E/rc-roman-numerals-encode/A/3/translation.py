from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, move, initialize, display_line, Stdin, SPACES,
)

_TABLE = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"),
    (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"),
    (5, "V"), (4, "IV"), (1, "I"),
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
    save = ws["WS-SAVE-NUMBER"]
    ocx = ws["OCX"]
    roman = ws["WS-ROMAN"]

    inp.accept(num)
    while num.value != 0:
        move(num, save)
        n = num.value
        if n > 0 and n < 4000:
            initialize(roman)
            move(0, ocx)
            rx = 1
            while num.value != 0:
                if rx > len(_TABLE):
                    break
                divisor, chars = _TABLE[rx - 1]
                while not (num.value < divisor):
                    for ch in chars:
                        o = int(ocx) + 1
                        move(o, ocx)
                        o = int(ocx)
                        if 1 <= o <= 16:
                            move(ch, ws.f("WS-ROMAN-CH", o))
                    move(num.value - divisor, num)
                rx += 1
            out += display_line("inp=", save, " roman=", roman)
        else:
            out += display_line("inp=", save, " invalid")
        inp.accept(num)

    return bytes(out), {}

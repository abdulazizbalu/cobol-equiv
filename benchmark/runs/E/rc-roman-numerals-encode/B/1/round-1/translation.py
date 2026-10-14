from decimal import Decimal

from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Filler, move, compute, dec, initialize,
    display_line, Stdin,
)


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Num("WS-NUMBER", "9(4)", value=0),
        Num("WS-SAVE-NUMBER", "9(4)"),
        Group("WS-TBL-DEF", [
            Filler("X(7)", "1000M  "),
            Filler("X(7)", "0900CM "),
            Filler("X(7)", "0500D  "),
            Filler("X(7)", "0400CD "),
            Filler("X(7)", "0100C  "),
            Filler("X(7)", "0090XC "),
            Filler("X(7)", "0050L  "),
            Filler("X(7)", "0040XL "),
            Filler("X(7)", "0010X  "),
            Filler("X(7)", "0009IX "),
            Filler("X(7)", "0005V  "),
            Filler("X(7)", "0004IV "),
            Filler("X(7)", "0001I  "),
        ]),
        Group("WS-TBL-R", [
            Group("WS-TBL-ENT", [
                Num("WS-TBL-DIVISOR", "9(4)"),
                Alnum("WS-TBL-ROMAN-CH", "X(1)", occurs=3),
            ], occurs=13),
        ], redefines="WS-TBL-DEF"),
        Num("OCX", "99"),
        Group("WS-ROMAN", [
            Alnum("WS-ROMAN-CH", "X(1)", occurs=16),
        ]),
    ])

    out = bytearray()
    inp = Stdin(stdin)
    num = ws["WS-NUMBER"]
    save = ws["WS-SAVE-NUMBER"]
    ocx = ws["OCX"]
    roman = ws["WS-ROMAN"]

    inp.accept(num)
    while not (num.value == 0):
        move(num, save)
        if num.value > 0 and num.value < 4000:
            initialize(roman)
            move(0, ocx)
            rx = 1
            while not (num.value == 0):
                div = ws.f("WS-TBL-DIVISOR", rx)
                while not (num.value < div.value):
                    cx = 1
                    while ws.f("WS-TBL-ROMAN-CH", rx, cx).raw != b" ":
                        compute(ocx, dec(ocx) + dec(1))
                        move(ws.f("WS-TBL-ROMAN-CH", rx, cx),
                             ws.f("WS-ROMAN-CH", int(ocx)))
                        cx += 1
                    compute(num, dec(num) - dec(div))
                rx += 1
            out += display_line("inp=", save, " roman=", roman)
        else:
            out += display_line("inp=", save, " invalid")
        inp.accept(num)

    return bytes(out), {}

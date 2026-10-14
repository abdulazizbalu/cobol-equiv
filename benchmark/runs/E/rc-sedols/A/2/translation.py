from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, COMP, move, add, compute, dec, initialize,
    display_line, refmod,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()

    fd = Storage("SEDOL-FILE", [Alnum("SEDOL", "X(6)")])
    ws = Storage("WS", [
        Alnum("SEDOL-FILE-STATUS", "XX"),
        Num("DIGIT-NUM", "9", usage=COMP),
        Group("DIGIT-WEIGHTS-AREA", [
            Num("DIGIT-WEIGHTS", "9", occurs=7),
        ]),
        Group("WEIGHTED-SUM-PARTS-AREA", [
            Num("WEIGHTED-SUM-PARTS", "9(3)", usage=COMP, occurs=6),
        ]),
        Num("WEIGHTED-SUM", "9(3)", usage=COMP),
        Num("CHECK-DIGIT", "9"),
    ])
    move("1317391", ws["DIGIT-WEIGHTS-AREA"])

    sedol = fd["SEDOL"]
    reader = LineSequentialReader(input_files.get("sedol.txt", b""), 6)
    move("00", ws["SEDOL-FILE-STATUS"])

    while ws["SEDOL-FILE-STATUS"].raw == b"00":
        r = reader.read(sedol)
        if r is None:
            move("10", ws["SEDOL-FILE-STATUS"])
            break
        move("00", ws["SEDOL-FILE-STATUS"])

        raw = sedol.raw
        up = bytes((b - 32) if 97 <= b <= 122 else b for b in raw)
        sedol.set_raw(up)

        for i in range(1, 7):
            move(i, ws["DIGIT-NUM"])
            c = sedol.raw[i - 1]
            weight = ws.f("DIGIT-WEIGHTS", i)
            part = ws.f("WEIGHTED-SUM-PARTS", i)
            if (65 <= c <= 90) or c == 32:
                if c in b"AEIOU":
                    out += display_line("Invalid SEDOL: ", sedol)
                    continue
                compute(part, (dec(c + 1) - dec(ord("A") + 1) + dec(10)) * dec(weight))
            elif 48 <= c <= 57:
                compute(part, dec(c - 48) * dec(weight))
            else:
                out += display_line("Invalid SEDOL: ", sedol)
                continue
        move(7, ws["DIGIT-NUM"])

        initialize(ws["WEIGHTED-SUM"])
        for i in range(1, 7):
            add(ws.f("WEIGHTED-SUM-PARTS", i), ws["WEIGHTED-SUM"])

        wsum = int(ws["WEIGHTED-SUM"])
        compute(ws["CHECK-DIGIT"], dec((10 - wsum % 10) % 10))

        out += display_line(sedol, ws["CHECK-DIGIT"])

    return bytes(out), {}

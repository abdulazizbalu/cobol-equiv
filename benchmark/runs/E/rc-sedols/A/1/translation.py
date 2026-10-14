from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, COMP, move, add, compute, dec,
    multiply_giving, initialize, display_line, refmod,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()

    rec = Storage("SEDOL-REC", [Alnum("sedol", "X(6)")])
    ws = Storage("WS", [
        Alnum("sedol-file-status", "XX"),
        Num("digit-num", "9", usage=COMP),
        Group("digit-weights-area", [
            Num("digit-weights", "9", occurs=7),
        ]),
        Group("weighted-sum-parts-area", [
            Num("weighted-sum-parts", "9(3)", usage=COMP, occurs=6),
        ]),
        Num("weighted-sum", "9(3)", usage=COMP),
        Num("check-digit", "9"),
    ])
    ws["digit-weights-area"].set_raw(b"1317391")

    sedol = rec["sedol"]
    reader = LineSequentialReader(input_files.get("sedol.txt", b""), 6)
    move("00", ws["sedol-file-status"])

    while ws["sedol-file-status"].raw == b"00":
        r = reader.read(sedol)
        if r is None:
            move("10", ws["sedol-file-status"])
            break
        move("00", ws["sedol-file-status"])

        raw = sedol.raw
        upper = bytes((b - 32) if 97 <= b <= 122 else b for b in raw)
        sedol.set_raw(upper)

        for i in range(1, 7):
            c = sedol.raw[i - 1]
            part = ws.f("weighted-sum-parts", i)
            weight = ws.f("digit-weights", i)
            if (65 <= c <= 90) or c == 32:
                if c in b"AEIOU":
                    out += display_line("Invalid SEDOL: ", sedol)
                    continue
                compute(part, dec(c - 65 + 10) * dec(weight))
            elif 48 <= c <= 57:
                multiply_giving(c - 48, weight, part)
            else:
                out += display_line("Invalid SEDOL: ", sedol)
                continue

        initialize(ws["weighted-sum"])
        for i in range(1, 7):
            add(ws.f("weighted-sum-parts", i), ws["weighted-sum"])

        s = int(ws["weighted-sum"])
        cd = (10 - (s % 10)) % 10
        move(cd, ws["check-digit"])

        out += display_line(sedol, ws["check-digit"])

    return bytes(out), {}

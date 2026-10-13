"""Reference translation of the Rosetta Code "SEDOLs" solution sedols.cob."""

from cobol_equiv.runtime import COMP, Num, Storage, add, compute, move
from cobol_equiv.runtime.files import LineSequentialReader

WEIGHTS = [1, 3, 1, 7, 3, 9, 1]


def main(stdin: bytes, input_files: dict) -> tuple:
    reader = LineSequentialReader(input_files["sedol.txt"], 6)
    ws = Storage("WS", [Num("PARTS", "9(3)", usage=COMP, occurs=6), Num("SUM", "9(3)", usage=COMP),
                        Num("CHECK", "9")])
    out = bytearray()
    while (rec := reader.read()) is not None:
        sedol = bytes(c - 32 if 0x61 <= c <= 0x7A else c for c in rec)
        for k in range(6):
            ch = sedol[k:k + 1]
            if b"A" <= ch <= b"Z" or ch == b" ":  # IS ALPHABETIC-UPPER includes space
                if ch in (b"A", b"E", b"I", b"O", b"U"):
                    out += b"Invalid SEDOL: " + sedol + b"\n"
                    continue
                compute(ws.f("PARTS", k + 1), (ch[0] - 65 + 10) * WEIGHTS[k])
            elif b"0" <= ch <= b"9":
                compute(ws.f("PARTS", k + 1), int(ch) * WEIGHTS[k])
            else:
                out += b"Invalid SEDOL: " + sedol + b"\n"
                continue
        move(0, ws["SUM"])
        for k in range(6):
            add(ws.f("PARTS", k + 1), ws["SUM"])
        compute(ws["CHECK"], (10 - int(ws["SUM"].value) % 10) % 10)
        out += sedol + ws["CHECK"].raw + b"\n"
    return bytes(out), {}

from cobol_equiv.runtime import Storage, Num, Alnum, Edited, Group, move, add, display_line
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    rec = Storage("IN-FILE", [
        Group("IN-REC", [
            Alnum("IN-CODE", "X"),
            Num("IN-AMT", "9(3)V99"),
        ]),
    ])
    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
        Num("WS-COUNT", "9(3)", value=0),
        Num("WS-TOTAL", "9(5)V99", value=0),
        Edited("WS-OUT", "ZZ,ZZ9.99"),
    ])

    out = bytearray()
    reader = LineSequentialReader(input_files.get("VALUES.DAT", b""), 6)

    while ws["WS-EOF"].raw != b"Y":
        r = reader.read(rec.record())
        if r is None:
            move("Y", ws["WS-EOF"])
        else:
            if rec["IN-CODE"].raw == b"A":
                add(1, ws["WS-COUNT"])
                add(rec["IN-AMT"], ws["WS-TOTAL"])

    move(ws["WS-TOTAL"], ws["WS-OUT"])
    out += display_line("COUNT ", ws["WS-COUNT"], " TOTAL ", ws["WS-OUT"])
    return bytes(out), {}

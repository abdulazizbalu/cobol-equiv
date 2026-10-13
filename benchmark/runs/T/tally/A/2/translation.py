from cobol_equiv.runtime import (
    Storage,
    Group,
    Num,
    Alnum,
    Edited,
    move,
    add,
    display_line,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    in_file = Storage("IN-FILE", [
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

    # OPEN INPUT IN-FILE
    reader = LineSequentialReader(input_files.get("VALUES.DAT", b""), 6)

    # PERFORM UNTIL WS-EOF = "Y"
    while ws["WS-EOF"].raw != b"Y":
        rec = reader.read(in_file["IN-REC"])
        if rec is None:
            move("Y", ws["WS-EOF"])
        else:
            if in_file["IN-CODE"].raw == b"B":
                add(1, ws["WS-COUNT"])
                add(in_file["IN-AMT"], ws["WS-TOTAL"])

    # CLOSE IN-FILE

    move(ws["WS-TOTAL"], ws["WS-OUT"])
    out += display_line("COUNT ", ws["WS-COUNT"], " TOTAL ", ws["WS-OUT"])

    return bytes(out), {}

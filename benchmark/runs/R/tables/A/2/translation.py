from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited, Filler, SPACES,
    move, add, compute, dec, display_line,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()

    rec = Storage("ITEM-REC", [
        Alnum("IT-CODE", "X(3)"),
        Num("IT-QTY", "9(3)"),
        Num("IT-PRICE", "9(3)V99"),
    ])

    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
        Group("WS-TABLE", [
            Group("WS-ENTRY", [
                Alnum("WS-CODE", "X(3)"),
                Num("WS-QTY", "9(5)"),
                Num("WS-AMT", "9(6)V99"),
            ], occurs=8),
        ]),
        Alnum("WS-SWAP", "X(16)"),
        Num("WS-COUNT", "99", value=0),
        Num("WS-REJECTED", "99", value=0),
        Num("WS-I", "99"),
        Num("WS-J", "99"),
        Group("WS-LINE", [
            Edited("WL-RANK", "Z9"),
            Filler("X", value=SPACES),
            Alnum("WL-CODE", "X(3)"),
            Filler("X", value=SPACES),
            Edited("WL-QTY", "ZZ,ZZ9"),
            Filler("X", value=SPACES),
            Edited("WL-AMT", "ZZZ,ZZ9.99"),
        ]),
    ])

    reader = LineSequentialReader(input_files.get("ITEMS.DAT", b""), 11)
    rec_ref = rec.record()

    def new_entry():
        if int(ws["WS-COUNT"]) < 8:
            add(1, ws["WS-COUNT"])
            c = int(ws["WS-COUNT"])
            move(rec["IT-CODE"], ws.f("WS-CODE", c))
            move(rec["IT-QTY"], ws.f("WS-QTY", c))
            compute(ws.f("WS-AMT", c), dec(rec["IT-QTY"]) * dec(rec["IT-PRICE"]))
        else:
            add(1, ws["WS-REJECTED"])
            out.extend(display_line("TABLE FULL ", rec["IT-CODE"]))

    def add_item():
        tx = 1
        while True:
            if tx > 8:
                new_entry()
                return
            if ws.f("WS-CODE", tx).raw == rec["IT-CODE"].raw:
                add(rec["IT-QTY"], ws.f("WS-QTY", tx))
                compute(ws.f("WS-AMT", tx),
                        dec(ws.f("WS-AMT", tx)) + dec(rec["IT-QTY"]) * dec(rec["IT-PRICE"]))
                return
            tx += 1

    while ws["WS-EOF"].raw != b"Y":
        r = reader.read(rec_ref)
        if r is None:
            move("Y", ws["WS-EOF"])
        else:
            add_item()

    # bubble sort
    count = int(ws["WS-COUNT"])
    i = 1
    while not (i >= count):
        j = 1
        while not (j > count - i):
            if ws.f("WS-AMT", j).value < ws.f("WS-AMT", j + 1).value:
                a = ws.f("WS-ENTRY", j)
                b = ws.f("WS-ENTRY", j + 1)
                ra, rb = a.raw, b.raw
                a.set_raw(rb)
                b.set_raw(ra)
            j += 1
        i += 1

    for i in range(1, count + 1):
        move(i, ws["WL-RANK"])
        move(ws.f("WS-CODE", i), ws["WL-CODE"])
        move(ws.f("WS-QTY", i), ws["WL-QTY"])
        move(ws.f("WS-AMT", i), ws["WL-AMT"])
        out.extend(display_line(ws["WS-LINE"]))

    out.extend(display_line("ITEMS ", ws["WS-COUNT"], " REJECTED ", ws["WS-REJECTED"]))
    return bytes(out), {}

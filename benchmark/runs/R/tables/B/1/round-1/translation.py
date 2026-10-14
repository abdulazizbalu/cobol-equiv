from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited, Filler,
    move, add, compute, dec, display_line, SPACES,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict) -> tuple:
    out = bytearray()

    fs = Storage("ITEM-FILE", [
        Group("ITEM-REC", [
            Alnum("IT-CODE", "X(3)"),
            Num("IT-QTY", "9(3)"),
            Num("IT-PRICE", "9(3)V99"),
        ]),
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

    rec = fs["ITEM-REC"]
    it_code = fs["IT-CODE"]
    it_qty = fs["IT-QTY"]
    it_price = fs["IT-PRICE"]
    ws_count = ws["WS-COUNT"]
    ws_rej = ws["WS-REJECTED"]
    ws_i = ws["WS-I"]
    ws_j = ws["WS-J"]

    def new_entry():
        if int(ws_count) < 8:
            add(1, ws_count)
            c = int(ws_count)
            move(it_code, ws.f("WS-CODE", c))
            move(it_qty, ws.f("WS-QTY", c))
            compute(ws.f("WS-AMT", c), dec(it_qty) * dec(it_price))
        else:
            add(1, ws_rej)
            out.extend(display_line("TABLE FULL ", it_code))

    def add_item():
        tx = 1
        while True:
            if tx > 8:
                new_entry()
                return
            if ws.f("WS-CODE", tx).raw == it_code.raw:
                add(it_qty, ws.f("WS-QTY", tx))
                compute(ws.f("WS-AMT", tx),
                        dec(ws.f("WS-AMT", tx)) + dec(it_qty) * dec(it_price))
                return
            tx += 1

    reader = LineSequentialReader(input_files.get("ITEMS.DAT", b""), 11)
    while ws["WS-EOF"].raw != b"Y":
        r = reader.read(rec)
        if r is None:
            move("Y", ws["WS-EOF"])
        else:
            add_item()

    # bubble sort
    move(1, ws_i)
    while not (int(ws_i) >= int(ws_count)):
        move(1, ws_j)
        while not (int(ws_j) > int(ws_count) - int(ws_i)):
            j = int(ws_j)
            if ws.f("WS-AMT", j).value < ws.f("WS-AMT", j + 1).value:
                move(ws.f("WS-ENTRY", j), ws["WS-SWAP"])
                move(ws.f("WS-ENTRY", j + 1), ws.f("WS-ENTRY", j))
                move(ws["WS-SWAP"], ws.f("WS-ENTRY", j + 1))
            add(1, ws_j)
        add(1, ws_i)

    move(1, ws_i)
    while not (int(ws_i) > int(ws_count)):
        i = int(ws_i)
        move(ws_i, ws["WL-RANK"])
        move(ws.f("WS-CODE", i), ws["WL-CODE"])
        move(ws.f("WS-QTY", i), ws["WL-QTY"])
        move(ws.f("WS-AMT", i), ws["WL-AMT"])
        out.extend(display_line(ws["WS-LINE"]))
        add(1, ws_i)

    out.extend(display_line("ITEMS ", ws_count, " REJECTED ", ws_rej))
    return bytes(out), {}

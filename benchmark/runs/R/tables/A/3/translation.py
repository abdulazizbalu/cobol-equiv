from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited, Filler,
    move, add, compute, dec, display_line, SPACES,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()

    rec = Storage("ITEM-REC", [
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

    it_code = rec["IT-CODE"]
    it_qty = rec["IT-QTY"]
    it_price = rec["IT-PRICE"]
    ws_count = ws["WS-COUNT"]
    ws_rej = ws["WS-REJECTED"]

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
    rec_ref = rec["ITEM-REC"]
    while ws["WS-EOF"].raw != b"Y":
        r = reader.read(rec_ref)
        if r is None:
            move("Y", ws["WS-EOF"])
        else:
            add_item()

    # Bubble sort
    i = 1
    while True:
        cnt = int(ws_count)
        if i >= cnt:
            break
        j = 1
        while True:
            cnt = int(ws_count)
            if j > cnt - i:
                break
            a = ws.f("WS-AMT", j).value
            b = ws.f("WS-AMT", j + 1).value
            if a < b:
                e1 = ws.f("WS-ENTRY", j)
                e2 = ws.f("WS-ENTRY", j + 1)
                tmp = e1.raw
                e1.set_raw(e2.raw)
                e2.set_raw(tmp)
            j += 1
        i += 1

    move(i % 100, ws["WS-I"])

    i = 1
    while i <= int(ws_count):
        move(i, ws["WS-I"])
        move(ws["WS-I"], ws["WL-RANK"])
        move(ws.f("WS-CODE", i), ws["WL-CODE"])
        move(ws.f("WS-QTY", i), ws["WL-QTY"])
        move(ws.f("WS-AMT", i), ws["WL-AMT"])
        out.extend(display_line(ws["WS-LINE"]))
        i += 1

    out.extend(display_line("ITEMS ", ws_count, " REJECTED ", ws_rej))
    return bytes(out), {}

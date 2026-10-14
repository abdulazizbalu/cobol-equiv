from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited, move, add, multiply, string,
    display_line, SPACES,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()

    rec = Storage("CELL-REC", [
        Num("CL-ROW", "9"),
        Num("CL-COL", "9"),
        Alnum("CL-OP", "X"),
        Num("CL-VAL", "S9(3)"),
    ])

    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
        Group("WS-MATRIX", [
            Group("WS-ROW", [
                Num("WS-CELL", "S9(4)", occurs=5),
            ], occurs=4),
        ]),
        Group("WS-TRANS", [
            Group("WT-ROW", [
                Num("WT-CELL", "S9(4)", occurs=4),
            ], occurs=5),
        ]),
        Num("WS-I", "9"),
        Num("WS-J", "9"),
        Num("WS-SUM", "S9(5)"),
        Num("WS-MAX", "S9(4)"),
        Num("WS-MAX-I", "9"),
        Num("WS-MAX-J", "9"),
        Num("WS-BAD", "99", value=0),
        Alnum("WS-LINE", "X(40)"),
        Num("WS-PTR", "99"),
        Edited("WS-ED", "-(4)9"),
    ])

    reader = LineSequentialReader(input_files.get("CELLS.DAT", b""), 6)
    rec_ref = rec.record()

    def apply_cell():
        r = int(rec["CL-ROW"].value)
        c = int(rec["CL-COL"].value)
        if r < 1 or r > 4 or c < 1 or c > 5:
            add(1, ws["WS-BAD"])
        else:
            op = rec["CL-OP"].text
            cell = ws.f("WS-CELL", r, c)
            if op == "=":
                move(rec["CL-VAL"], cell)
            elif op == "+":
                add(rec["CL-VAL"], cell)
            elif op == "*":
                multiply(rec["CL-VAL"], cell)
            else:
                add(1, ws["WS-BAD"])

    while ws["WS-EOF"].text != "Y":
        data = reader.read(rec_ref)
        if data is None:
            move("Y", ws["WS-EOF"])
        else:
            apply_cell()

    for i in range(1, 5):
        move(i, ws["WS-I"])
        for j in range(1, 6):
            move(j, ws["WS-J"])
            move(ws.f("WS-CELL", i, j), ws.f("WT-CELL", j, i))
    move(5, ws["WS-I"])

    move(ws.f("WS-CELL", 1, 1), ws["WS-MAX"])
    move(1, ws["WS-MAX-I"], ws["WS-MAX-J"])

    def check_max(i, j):
        cell = ws.f("WS-CELL", i, j)
        if cell.value > ws["WS-MAX"].value:
            move(cell, ws["WS-MAX"])
            move(ws["WS-I"], ws["WS-MAX-I"])
            move(ws["WS-J"], ws["WS-MAX-J"])

    def print_row(i):
        move(SPACES, ws["WS-LINE"])
        move(1, ws["WS-PTR"])
        move(0, ws["WS-SUM"])
        for j in range(1, 6):
            move(j, ws["WS-J"])
            check_max(i, j)
            add(ws.f("WS-CELL", i, j), ws["WS-SUM"])
            move(ws.f("WS-CELL", i, j), ws["WS-ED"])
            string([(ws["WS-ED"], None), (" ", None)], ws["WS-LINE"],
                   pointer=ws["WS-PTR"])
        move(6, ws["WS-J"])
        move(ws["WS-SUM"], ws["WS-ED"])
        out.extend(display_line(ws["WS-LINE"], "= ", ws["WS-ED"]))

    for i in range(1, 5):
        move(i, ws["WS-I"])
        print_row(i)
    move(5, ws["WS-I"])

    for j in range(1, 6):
        move(j, ws["WS-J"])
        move(0, ws["WS-SUM"])
        for i in range(1, 5):
            move(i, ws["WS-I"])
            add(ws.f("WT-CELL", j, i), ws["WS-SUM"])
        move(5, ws["WS-I"])
        move(ws["WS-SUM"], ws["WS-ED"])
        out.extend(display_line("COL ", ws["WS-J"], " ", ws["WS-ED"]))
    move(6, ws["WS-J"])

    out.extend(display_line("MAX ", ws["WS-MAX"], " AT ", ws["WS-MAX-I"], ",",
                            ws["WS-MAX-J"], " BAD ", ws["WS-BAD"]))

    return bytes(out), {}

from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited, move, add, multiply,
    display_line, string, SPACES,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = []

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

    def cell(i, j):
        return ws.f("WS-CELL", i, j)

    def apply_cell():
        r = rec["CL-ROW"].value
        c = rec["CL-COL"].value
        if r < 1 or r > 4 or c < 1 or c > 5:
            add(1, ws["WS-BAD"])
        else:
            op = rec["CL-OP"].text
            ri = int(r)
            ci = int(c)
            if op == "=":
                move(rec["CL-VAL"], cell(ri, ci))
            elif op == "+":
                add(rec["CL-VAL"], cell(ri, ci))
            elif op == "*":
                multiply(rec["CL-VAL"], cell(ri, ci))
            else:
                add(1, ws["WS-BAD"])

    def check_max():
        i = int(ws["WS-I"])
        j = int(ws["WS-J"])
        if cell(i, j).value > ws["WS-MAX"].value:
            move(cell(i, j), ws["WS-MAX"])
            move(ws["WS-I"], ws["WS-MAX-I"])
            move(ws["WS-J"], ws["WS-MAX-J"])

    def print_row():
        move(SPACES, ws["WS-LINE"])
        move(1, ws["WS-PTR"])
        move(0, ws["WS-SUM"])
        move(1, ws["WS-J"])
        while not int(ws["WS-J"]) > 5:
            check_max()
            i = int(ws["WS-I"])
            j = int(ws["WS-J"])
            add(cell(i, j), ws["WS-SUM"])
            move(cell(i, j), ws["WS-ED"])
            string([(ws["WS-ED"], None), (" ", None)], ws["WS-LINE"], pointer=ws["WS-PTR"])
            add(1, ws["WS-J"])
        move(ws["WS-SUM"], ws["WS-ED"])
        out.append(display_line(ws["WS-LINE"], "= ", ws["WS-ED"]))

    reader = LineSequentialReader(input_files.get("CELLS.DAT", b""), 6)
    while ws["WS-EOF"].text != "Y":
        if reader.read(rec.record()) is None:
            move("Y", ws["WS-EOF"])
        else:
            apply_cell()

    move(1, ws["WS-I"])
    while not int(ws["WS-I"]) > 4:
        move(1, ws["WS-J"])
        while not int(ws["WS-J"]) > 5:
            i = int(ws["WS-I"])
            j = int(ws["WS-J"])
            move(cell(i, j), ws.f("WT-CELL", j, i))
            add(1, ws["WS-J"])
        add(1, ws["WS-I"])

    move(cell(1, 1), ws["WS-MAX"])
    move(1, ws["WS-MAX-I"], ws["WS-MAX-J"])

    move(1, ws["WS-I"])
    while not int(ws["WS-I"]) > 4:
        print_row()
        add(1, ws["WS-I"])

    move(1, ws["WS-J"])
    while not int(ws["WS-J"]) > 5:
        move(0, ws["WS-SUM"])
        move(1, ws["WS-I"])
        while not int(ws["WS-I"]) > 4:
            add(ws.f("WT-CELL", int(ws["WS-J"]), int(ws["WS-I"])), ws["WS-SUM"])
            add(1, ws["WS-I"])
        move(ws["WS-SUM"], ws["WS-ED"])
        out.append(display_line("COL ", ws["WS-J"], " ", ws["WS-ED"]))
        add(1, ws["WS-J"])

    out.append(display_line("MAX ", ws["WS-MAX"], " AT ", ws["WS-MAX-I"], ",",
                            ws["WS-MAX-J"], " BAD ", ws["WS-BAD"]))

    return b"".join(out), {}

"""Reference Python translation of benchmark/corpus-r/matrix/program.cob
(MIT licensed)."""

from cobol_equiv.runtime import (SPACES, Alnum, Edited, Group, Num, Storage, add, display_line,
                                 move, multiply, string)
from cobol_equiv.runtime.files import LineSequentialReader

CELL_REC = [Num("CL-ROW", "9"), Num("CL-COL", "9"), Alnum("CL-OP", "X"), Num("CL-VAL", "S9(3)")]


def working_storage():
    return Storage("WS", [
        Group("WS-MATRIX", [Group("WS-ROW", [Num("WS-CELL", "S9(4)", occurs=5)], occurs=4)]),
        Group("WS-TRANS", [Group("WT-ROW", [Num("WT-CELL", "S9(4)", occurs=4)], occurs=5)]),
        Num("WS-I", "9"), Num("WS-J", "9"), Num("WS-SUM", "S9(5)"), Num("WS-MAX", "S9(4)"),
        Num("WS-MAX-I", "9"), Num("WS-MAX-J", "9"), Num("WS-BAD", "99", value=0),
        Alnum("WS-LINE", "X(40)"), Num("WS-PTR", "99"), Edited("WS-ED", "-(4)9"),
    ])


def apply_cell(cl, ws):
    r, c = int(cl["CL-ROW"].value), int(cl["CL-COL"].value)
    if r < 1 or r > 4 or c < 1 or c > 5:
        add(1, ws["WS-BAD"])
        return
    op = cl["CL-OP"].raw
    cell = ws.f("WS-CELL", r, c)
    if op == b"=":
        move(cl["CL-VAL"], cell)
    elif op == b"+":
        add(cl["CL-VAL"], cell)
    elif op == b"*":
        multiply(cl["CL-VAL"], cell)
    else:
        add(1, ws["WS-BAD"])


def check_max(ws, i, j):
    if ws.f("WS-CELL", i, j).value > ws["WS-MAX"].value:
        move(ws.f("WS-CELL", i, j), ws["WS-MAX"])
        move(i, ws["WS-MAX-I"])
        move(j, ws["WS-MAX-J"])


def print_row(ws, i, out):
    move(SPACES, ws["WS-LINE"])
    move(1, ws["WS-PTR"])
    move(0, ws["WS-SUM"])
    for j in range(1, 6):
        move(j, ws["WS-J"])
        check_max(ws, i, j)
        add(ws.f("WS-CELL", i, j), ws["WS-SUM"])
        move(ws.f("WS-CELL", i, j), ws["WS-ED"])
        string([(ws["WS-ED"], None), (" ", None)], ws["WS-LINE"], pointer=ws["WS-PTR"])
    move(6, ws["WS-J"])
    move(ws["WS-SUM"], ws["WS-ED"])
    out += display_line(ws["WS-LINE"], "= ", ws["WS-ED"])


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = working_storage()
    cl = Storage("CELL-REC", CELL_REC)
    reader = LineSequentialReader(input_files["CELLS.DAT"], cl.size)
    out = bytearray()
    while reader.read(cl.record()) is not None:
        apply_cell(cl, ws)
    for i in range(1, 5):
        for j in range(1, 6):
            move(ws.f("WS-CELL", i, j), ws.f("WT-CELL", j, i))
    move(ws.f("WS-CELL", 1, 1), ws["WS-MAX"])
    move(1, ws["WS-MAX-I"], ws["WS-MAX-J"])
    for i in range(1, 5):
        move(i, ws["WS-I"])
        print_row(ws, i, out)
    for j in range(1, 6):
        move(j, ws["WS-J"])
        move(0, ws["WS-SUM"])
        for i in range(1, 5):
            add(ws.f("WT-CELL", j, i), ws["WS-SUM"])
        move(ws["WS-SUM"], ws["WS-ED"])
        out += display_line("COL ", ws["WS-J"], " ", ws["WS-ED"])
    out += display_line("MAX ", ws["WS-MAX"], " AT ", ws["WS-MAX-I"], ",", ws["WS-MAX-J"], " BAD ",
                        ws["WS-BAD"])
    return bytes(out), {}

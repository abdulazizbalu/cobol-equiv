"""Reference Python translation of corpus/tables/program.cob (MIT licensed)."""

from cobol_equiv.runtime import (Alnum, Edited, Filler, Group, Num, Storage, add, compute, dec,
                                 display_line, move)
from cobol_equiv.runtime.files import LineSequentialReader

ITEM_REC = [Alnum("IT-CODE", "X(3)"), Num("IT-QTY", "9(3)"), Num("IT-PRICE", "9(3)V99")]
SIZE = 8


def working_storage():
    return Storage("WS", [
        Group("WS-TABLE", [
            Group("WS-ENTRY", [Alnum("WS-CODE", "X(3)"), Num("WS-QTY", "9(5)"),
                               Num("WS-AMT", "9(6)V99")], occurs=SIZE),
        ]),
        Alnum("WS-SWAP", "X(16)"),
        Num("WS-COUNT", "99", value=0),
        Num("WS-REJECTED", "99", value=0),
        Num("WS-I", "99"),
        Num("WS-J", "99"),
        Group("WS-LINE", [
            Edited("WL-RANK", "Z9"), Filler("X", " "), Alnum("WL-CODE", "X(3)"), Filler("X", " "),
            Edited("WL-QTY", "ZZ,ZZ9"), Filler("X", " "), Edited("WL-AMT", "ZZZ,ZZ9.99"),
        ]),
    ])


def add_item(it, ws, out):
    # SET TX TO 1 / SEARCH WS-ENTRY: scans all 8 occurrences
    for tx in range(1, SIZE + 1):
        if ws.f("WS-CODE", tx).raw == it["IT-CODE"].raw:
            add(it["IT-QTY"], ws.f("WS-QTY", tx))
            compute(ws.f("WS-AMT", tx), dec(ws.f("WS-AMT", tx)) + dec(it["IT-QTY"]) * dec(it["IT-PRICE"]))
            return
    new_entry(it, ws, out)


def new_entry(it, ws, out):
    if ws["WS-COUNT"].value < SIZE:
        add(1, ws["WS-COUNT"])
        n = int(ws["WS-COUNT"].value)
        move(it["IT-CODE"], ws.f("WS-CODE", n))
        move(it["IT-QTY"], ws.f("WS-QTY", n))
        compute(ws.f("WS-AMT", n), dec(it["IT-QTY"]) * dec(it["IT-PRICE"]))
    else:
        add(1, ws["WS-REJECTED"])
        out += display_line("TABLE FULL ", it["IT-CODE"])


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = working_storage()
    it = Storage("ITEM-REC", ITEM_REC)
    reader = LineSequentialReader(input_files["ITEMS.DAT"], it.size)
    out = bytearray()
    while reader.read(it.record()) is not None:
        add_item(it, ws, out)
    # PERFORM VARYING WS-I ... AFTER WS-J ...
    move(1, ws["WS-I"])
    while not ws["WS-I"].value >= ws["WS-COUNT"].value:
        move(1, ws["WS-J"])
        while not ws["WS-J"].value > ws["WS-COUNT"].value - ws["WS-I"].value:
            j = int(ws["WS-J"].value)
            if ws.f("WS-AMT", j).value < ws.f("WS-AMT", j + 1).value:
                move(ws.f("WS-ENTRY", j), ws["WS-SWAP"])
                move(ws.f("WS-ENTRY", j + 1), ws.f("WS-ENTRY", j))
                move(ws["WS-SWAP"], ws.f("WS-ENTRY", j + 1))
            add(1, ws["WS-J"])
        add(1, ws["WS-I"])
    move(1, ws["WS-I"])
    while not ws["WS-I"].value > ws["WS-COUNT"].value:
        i = int(ws["WS-I"].value)
        move(ws["WS-I"], ws["WL-RANK"])
        move(ws.f("WS-CODE", i), ws["WL-CODE"])
        move(ws.f("WS-QTY", i), ws["WL-QTY"])
        move(ws.f("WS-AMT", i), ws["WL-AMT"])
        out += display_line(ws["WS-LINE"])
        add(1, ws["WS-I"])
    out += display_line("ITEMS ", ws["WS-COUNT"], " REJECTED ", ws["WS-REJECTED"])
    return bytes(out), {}

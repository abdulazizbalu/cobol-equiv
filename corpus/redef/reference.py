"""Reference Python translation of corpus/redef/program.cob (MIT licensed)."""

from cobol_equiv.runtime import (Alnum, Edited, Filler, Group, Num, Storage, add, compute, dec,
                                 display_line, move)
from cobol_equiv.runtime.files import LineSequentialReader

IN_REC = [
    Alnum("IR-TYPE", "X"),
    Alnum("IR-BODY", "X(29)"),
    Group("IR-HEADER", [
        Alnum("IH-NAME", "X(20)"),
        Num("IH-DATE", "9(8)"),
        Group("IH-DATE-R", [Num("IH-YYYY", "9(4)"), Num("IH-MM", "99"), Num("IH-DD", "99")],
              redefines="IH-DATE"),
        Filler("X"),
    ], redefines="IR-BODY"),
    Group("IR-DETAIL", [
        Alnum("ID-ITEM", "X(5)"), Num("ID-QTY", "S9(4)"), Num("ID-PRICE", "9(5)V99"),
        Num("ID-DISC", "V99"), Filler("X(11)"),
    ], redefines="IR-BODY"),
    Group("IR-TRAILER", [
        Num("IT-COUNT", "9(5)"), Num("IT-TOTAL", "S9(9)V99"), Filler("X(13)"),
    ], redefines="IR-BODY"),
]


def working_storage():
    return Storage("WS", [
        Alnum("WS-DAYS-TEXT", "X(24)", value="312931303130313130313031"),
        Group("WS-DAYS-TABLE", [Num("WS-DAYS", "99", occurs=12)], redefines="WS-DAYS-TEXT"),
        Num("WS-RUN-COUNT", "9(5)", value=0),
        Num("WS-RUN-TOTAL", "S9(9)V99", value=0),
        Num("WS-LINE-AMT", "S9(9)V99"),
        Edited("WS-LINE-ED", "---,---,--9.99"),
        Alnum("WS-DATE-OK", "X"),
    ])


def do_header(r, ws, out):
    move("Y", ws["WS-DATE-OK"])
    mm = r["IH-MM"].value
    if mm < 1 or mm > 12:
        move("N", ws["WS-DATE-OK"])
    elif r["IH-DD"].value < 1 or r["IH-DD"].value > ws.f("WS-DAYS", int(mm)).value:
        move("N", ws["WS-DATE-OK"])
    out += display_line("HEADER ", r["IH-NAME"], " ", r["IH-YYYY"], "-", r["IH-MM"], "-", r["IH-DD"],
                        " ", ws["WS-DATE-OK"], " ", r["IH-DATE"])


def do_detail(r, ws, out):
    compute(ws["WS-LINE-AMT"], dec(r["ID-QTY"]) * dec(r["ID-PRICE"]) * (1 - dec(r["ID-DISC"])),
            rounded=True)
    move(ws["WS-LINE-AMT"], ws["WS-LINE-ED"])
    add(1, ws["WS-RUN-COUNT"])
    add(ws["WS-LINE-AMT"], ws["WS-RUN-TOTAL"])
    out += display_line("DETAIL ", r["ID-ITEM"], " ", ws["WS-LINE-ED"])


def do_trailer(r, ws, out):
    if (r["IT-COUNT"].value == ws["WS-RUN-COUNT"].value
            and r["IT-TOTAL"].value == ws["WS-RUN-TOTAL"].value):
        out += display_line("TRAILER OK ", r["IT-COUNT"])
    else:
        out += display_line("TRAILER MISMATCH ", r["IT-COUNT"], " ", r["IT-TOTAL"], " ",
                            ws["WS-RUN-COUNT"], " ", ws["WS-RUN-TOTAL"])
    move(0, ws["WS-RUN-COUNT"], ws["WS-RUN-TOTAL"])


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = working_storage()
    r = Storage("IN-REC", IN_REC)
    reader = LineSequentialReader(input_files["RECS.DAT"], r.size)
    out = bytearray()
    while reader.read(r.record()) is not None:
        t = r["IR-TYPE"].raw
        if t == b"H":
            do_header(r, ws, out)
        elif t == b"D":
            do_detail(r, ws, out)
        elif t == b"T":
            do_trailer(r, ws, out)
        else:
            out += display_line("UNKNOWN TYPE ", r["IR-TYPE"])
    out += display_line("OPEN COUNT ", ws["WS-RUN-COUNT"], " TOTAL ", ws["WS-RUN-TOTAL"])
    return bytes(out), {}

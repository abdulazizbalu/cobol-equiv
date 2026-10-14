from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited, Filler,
    move, add, compute, dec, display_line,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    rec = Storage("IN-REC", [
        Alnum("IR-TYPE", "X"),
        Alnum("IR-BODY", "X(29)"),
        Group("IR-HEADER", [
            Alnum("IH-NAME", "X(20)"),
            Num("IH-DATE", "9(8)"),
            Group("IH-DATE-R", [
                Num("IH-YYYY", "9(4)"),
                Num("IH-MM", "99"),
                Num("IH-DD", "99"),
            ], redefines="IH-DATE"),
            Filler("X"),
        ], redefines="IR-BODY"),
        Group("IR-DETAIL", [
            Alnum("ID-ITEM", "X(5)"),
            Num("ID-QTY", "S9(4)"),
            Num("ID-PRICE", "9(5)V99"),
            Num("ID-DISC", "V99"),
            Filler("X(11)"),
        ], redefines="IR-BODY"),
        Group("IR-TRAILER", [
            Num("IT-COUNT", "9(5)"),
            Num("IT-TOTAL", "S9(9)V99"),
            Filler("X(13)"),
        ], redefines="IR-BODY"),
    ])

    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
        Alnum("WS-DAYS-TEXT", "X(24)", value="312931303130313130313031"),
        Group("WS-DAYS-TABLE", [
            Num("WS-DAYS", "99", occurs=12),
        ], redefines="WS-DAYS-TEXT"),
        Num("WS-RUN-COUNT", "9(5)", value=0),
        Num("WS-RUN-TOTAL", "S9(9)V99", value=0),
        Num("WS-LINE-AMT", "S9(9)V99"),
        Edited("WS-LINE-ED", "---,---,--9.99"),
        Alnum("WS-DATE-OK", "X"),
    ])

    out = bytearray()
    reader = LineSequentialReader(input_files.get("RECS.DAT", b""), 30)

    def do_header():
        move("Y", ws["WS-DATE-OK"])
        mm = rec["IH-MM"].value
        if mm < 1 or mm > 12:
            move("N", ws["WS-DATE-OK"])
        else:
            dd = rec["IH-DD"].value
            if dd < 1 or dd > ws.f("WS-DAYS", int(mm)).value:
                move("N", ws["WS-DATE-OK"])
        out.extend(display_line(
            "HEADER ", rec["IH-NAME"], " ", rec["IH-YYYY"], "-", rec["IH-MM"],
            "-", rec["IH-DD"], " ", ws["WS-DATE-OK"], " ", rec["IH-DATE"]))

    def do_detail():
        compute(ws["WS-LINE-AMT"],
                dec(rec["ID-QTY"]) * dec(rec["ID-PRICE"]) * (dec(1) - dec(rec["ID-DISC"])),
                rounded=True)
        move(ws["WS-LINE-AMT"], ws["WS-LINE-ED"])
        add(1, ws["WS-RUN-COUNT"])
        add(ws["WS-LINE-AMT"], ws["WS-RUN-TOTAL"])
        out.extend(display_line("DETAIL ", rec["ID-ITEM"], " ", ws["WS-LINE-ED"]))

    def do_trailer():
        if (rec["IT-COUNT"].value == ws["WS-RUN-COUNT"].value
                and rec["IT-TOTAL"].value == ws["WS-RUN-TOTAL"].value):
            out.extend(display_line("TRAILER OK ", rec["IT-COUNT"]))
        else:
            out.extend(display_line(
                "TRAILER MISMATCH ", rec["IT-COUNT"], " ", rec["IT-TOTAL"],
                " ", ws["WS-RUN-COUNT"], " ", ws["WS-RUN-TOTAL"]))
        move(0, ws["WS-RUN-COUNT"], ws["WS-RUN-TOTAL"])

    def do_record():
        t = rec["IR-TYPE"].raw
        if t == b"H":
            do_header()
        elif t == b"D":
            do_detail()
        elif t == b"T":
            do_trailer()
        else:
            out.extend(display_line("UNKNOWN TYPE ", rec["IR-TYPE"]))

    while ws["WS-EOF"].raw != b"Y":
        r = reader.read(rec.record())
        if r is None:
            move("Y", ws["WS-EOF"])
        else:
            do_record()

    out.extend(display_line("OPEN COUNT ", ws["WS-RUN-COUNT"], " TOTAL ", ws["WS-RUN-TOTAL"]))
    return bytes(out), {}

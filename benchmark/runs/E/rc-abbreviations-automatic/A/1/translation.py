from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, move, add, unstring, display_line, SPACES,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict) -> tuple:
    fd = Storage("FD", [Alnum("DOW-FILE", "X(200)")])
    ws = Storage("WS", [
        Alnum("DOW-LINE", "X(200)"),
        Num("ENDO", "9(1)"),
        Num("ENDO2", "9(1)"),
        Alnum("CURDAY", "X(50)"),
        Num("ABPTR", "999"),
        Num("LINE-NUM", "9(3)", value=1),
        Num("CHARAMT", "9(3)", value=1),
        Num("LARGESTCHARAMT", "9(3)"),
        Num("DAYNUM", "9(3)", value=1),
        Num("ABRESTART", "9(1)"),
        Alnum("CURABBR", "X(50)"),
        Num("TMP1", "9(3)"),
        Num("TMP2", "9(3)"),
        Num("TINDEX", "9(3)", value=1),
        Group("ABBRLIST", [Alnum("ABBRITEM", "X(50)", occurs=7)]),
    ])
    CURDAY_OFF = 202

    out = bytearray()
    reader = LineSequentialReader(input_files.get("days-of-week.txt", b""), 200)

    dow_line = ws["DOW-LINE"]
    curday = ws["CURDAY"]
    curabbr = ws["CURABBR"]

    while int(ws["ENDO"]) != 1:
        rec = reader.read(fd["DOW-FILE"])
        if rec is None:
            move(1, ws["ENDO"])
        else:
            move(fd["DOW-FILE"], dow_line)
            if dow_line.raw.strip(b" ") == b"":
                out += display_line("")
            else:
                move(0, ws["ENDO2"])
                move(0, ws["CHARAMT"])
                while int(ws["ENDO2"]) <= 0:
                    move(1, ws["ABPTR"])
                    move(1, ws["DAYNUM"])
                    move(0, ws["ABRESTART"])
                    add(1, ws["CHARAMT"])
                    for i in range(1, 8):
                        move(SPACES, ws.f("ABBRITEM", i))
                    move(8, ws["TINDEX"])
                    for _ in range(7):
                        unstring(dow_line, [" "], [curday], pointer=ws["ABPTR"])
                        raw = curday.raw
                        tmp1 = 50 - raw.count(b" ")
                        move(tmp1, ws["TMP1"])
                        move(raw.count(b" "), ws["TMP2"])
                        if int(ws["TMP1"]) > int(ws["LARGESTCHARAMT"]):
                            move(ws["TMP1"], ws["LARGESTCHARAMT"])
                        if raw.strip(b" ") == b"":
                            move(3, ws["ENDO2"])
                        n = int(ws["CHARAMT"])
                        area = ws.record().raw
                        piece = area[CURDAY_OFF:CURDAY_OFF + n]
                        if piece:
                            move(piece, curabbr)
                        else:
                            move(SPACES, curabbr)
                        ca = curabbr.raw
                        for i in range(1, 8):
                            if ws.f("ABBRITEM", i).raw == ca:
                                move(1, ws["ABRESTART"])
                        move(8, ws["TINDEX"])
                        dn = int(ws["DAYNUM"])
                        if 1 <= dn <= 7:
                            move(curabbr, ws.f("ABBRITEM", dn))
                        add(1, ws["DAYNUM"])
                    if int(ws["ABRESTART"]) == 0:
                        move(1, ws["ENDO2"])
                    if int(ws["CHARAMT"]) > int(ws["LARGESTCHARAMT"]):
                        move(2, ws["ENDO2"])

                out += display_line("Line ", ws["LINE-NUM"], ": ")[:-1]
                e2 = int(ws["ENDO2"])
                if e2 == 3:
                    out += b"Error: not enough "
                    out += b"days\n"
                elif e2 == 2:
                    out += b"Error: identical "
                    out += b"days\n"
                else:
                    out += display_line(ws["CHARAMT"], ": ")[:-1]
                    for t in range(1, 8):
                        move(ws.f("ABBRITEM", t), curabbr)
                        raw = curabbr.raw
                        trailing = len(raw) - len(raw.rstrip(b" "))
                        tmp1 = 50 - trailing
                        move(tmp1, ws["TMP1"])
                        move(trailing, ws["TMP2"])
                        if tmp1 > 0:
                            out += raw[:tmp1]
                        out += b"."
                        if t < 7:
                            out += b" "
                        else:
                            out += b"\n"
                    move(8, ws["TINDEX"])
        add(1, ws["LINE-NUM"])

    return bytes(out), {}

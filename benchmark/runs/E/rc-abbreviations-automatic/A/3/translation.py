from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, move, add, unstring, display_bytes, refmod,
    SPACES,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    fs = Storage("FS", [Alnum("DOW-FILE", "X(200)")])
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
    out = bytearray()
    reader = LineSequentialReader(input_files.get("days-of-week.txt", b""), 200)

    dow_line = ws["DOW-LINE"]
    curday = ws["CURDAY"]
    curabbr = ws["CURABBR"]
    charamt = ws["CHARAMT"]
    largest = ws["LARGESTCHARAMT"]
    endo2 = ws["ENDO2"]

    def all_spaces(f):
        return f.raw == b" " * len(f.raw)

    while int(ws["ENDO"]) != 1:
        rec = reader.read(fs["DOW-FILE"])
        if rec is None:
            move(1, ws["ENDO"])
        else:
            move(fs["DOW-FILE"], dow_line)
            if all_spaces(dow_line):
                out += b" \n"
            else:
                move(0, endo2)
                move(0, charamt)
                while int(endo2) <= 0:
                    move(1, ws["ABPTR"])
                    daynum = 1
                    move(0, ws["ABRESTART"])
                    add(1, charamt)
                    for t in range(1, 8):
                        move(SPACES, ws.f("ABBRITEM", t))
                    for _ in range(7):
                        unstring(dow_line, [" "], [curday], pointer=ws["ABPTR"])
                        nonspace = sum(1 for b in curday.raw if b != 0x20)
                        move(nonspace, ws["TMP1"])
                        if int(ws["TMP1"]) > int(largest):
                            move(ws["TMP1"], largest)
                        if all_spaces(curday):
                            move(3, endo2)
                        n = int(charamt)
                        ln = min(n, 50)
                        if ln > 0:
                            move(refmod(curday, 1, ln), curabbr)
                        else:
                            move(SPACES, curabbr)
                        for t in range(1, 8):
                            if ws.f("ABBRITEM", t).raw == curabbr.raw:
                                move(1, ws["ABRESTART"])
                        move(curabbr, ws.f("ABBRITEM", daynum))
                        daynum += 1
                    if int(ws["ABRESTART"]) == 0:
                        move(1, endo2)
                    if int(charamt) > int(largest):
                        move(2, endo2)
                out += b"Line " + display_bytes(ws["LINE-NUM"]) + b": "
                e = int(endo2)
                if e == 3:
                    out += b"Error: not enough days\n"
                elif e == 2:
                    out += b"Error: identical days\n"
                else:
                    out += display_bytes(charamt) + b": "
                    for t in range(1, 8):
                        move(ws.f("ABBRITEM", t), curabbr)
                        txt = curabbr.raw.rstrip(b" ")
                        out += txt
                        out += b"."
                        if t < 7:
                            out += b" "
                        else:
                            out += b"\n"
        add(1, ws["LINE-NUM"])

    return bytes(out), {}

from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited,
    move, add, subtract, compute, dec,
    divide_giving, divide_remainder, display_line,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    rec = Storage("DATE-REC", [
        Num("DT-FROM", "9(8)"),
        Num("DT-TO", "9(8)"),
        Num("DT-OFFSET", "S9(6)"),
    ])
    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
        Alnum("WS-CUM-TEXT", "X(36)", value="000031059090120151181212243273304334"),
        Group("WS-CUM-TABLE", [Num("WS-CUM", "999", occurs=12)], redefines="WS-CUM-TEXT"),
        Alnum("WS-DIM-TEXT", "X(24)", value="312831303130313130313031"),
        Group("WS-DIM-TABLE", [Num("WS-DIM", "99", occurs=12)], redefines="WS-DIM-TEXT"),
        Alnum("WS-DOW-TEXT", "X(21)", value="MONTUEWEDTHUFRISATSUN"),
        Group("WS-DOW-TABLE", [Alnum("WS-DOW-NAME", "X(3)", occurs=7)], redefines="WS-DOW-TEXT"),
        Num("WS-DATE", "9(8)"),
        Group("WS-DATE-R", [Num("WS-YYYY", "9(4)"), Num("WS-MM", "99"), Num("WS-DD", "99")],
              redefines="WS-DATE"),
        Alnum("WS-VALID", "X"),
        Alnum("WS-LEAP", "X"),
        Num("WS-Q", "9(7)"),
        Num("WS-R4", "9(4)"),
        Num("WS-R100", "9(4)"),
        Num("WS-R400", "9(4)"),
        Num("WS-Y", "9(5)"),
        Num("WS-DAYNUM", "S9(8)"),
        Num("WS-FROM-NUM", "S9(8)"),
        Num("WS-TO-NUM", "S9(8)"),
        Num("WS-NEW-NUM", "S9(8)"),
        Num("WS-DIFF", "S9(8)"),
        Edited("WS-DIFF-ED", "-(7)9"),
        Num("WS-DOW-IX", "9"),
        Num("WS-REM7", "9"),
        Num("WS-MAXDAY", "99"),
        Alnum("WS-RESULT", "X(8)"),
        Num("WS-TRY", "S9(8)"),
        Alnum("WS-DONE", "X"),
    ])
    W = ws.__getitem__
    out = bytearray()

    def check_leap():
        divide_remainder(W("WS-YYYY"), 4, W("WS-Q"), W("WS-R4"))
        divide_remainder(W("WS-YYYY"), 100, W("WS-Q"), W("WS-R100"))
        divide_remainder(W("WS-YYYY"), 400, W("WS-Q"), W("WS-R400"))
        if W("WS-R4").value == 0 and (W("WS-R100").value != 0 or W("WS-R400").value == 0):
            move("Y", W("WS-LEAP"))
        else:
            move("N", W("WS-LEAP"))

    def validate_date():
        move("Y", W("WS-VALID"))
        mm = W("WS-MM").value
        if W("WS-YYYY").value < 1601 or mm < 1 or mm > 12 or W("WS-DD").value < 1:
            move("N", W("WS-VALID"))
        else:
            check_leap()
            move(ws.f("WS-DIM", int(W("WS-MM"))), W("WS-MAXDAY"))
            if W("WS-MM").value == 2 and W("WS-LEAP").text == "Y":
                add(1, W("WS-MAXDAY"))
            if W("WS-DD").value > W("WS-MAXDAY").value:
                move("N", W("WS-VALID"))

    def date_to_num():
        compute(W("WS-Y"), dec(W("WS-YYYY")) - dec(1601))
        divide_giving(W("WS-Y"), 4, W("WS-Q"))
        compute(W("WS-DAYNUM"), dec(W("WS-Y")) * dec(365) + dec(W("WS-Q")))
        divide_giving(W("WS-Y"), 100, W("WS-Q"))
        subtract(W("WS-Q"), W("WS-DAYNUM"))
        divide_giving(W("WS-Y"), 400, W("WS-Q"))
        add(W("WS-Q"), W("WS-DAYNUM"))
        add([ws.f("WS-CUM", int(W("WS-MM"))), W("WS-DD")], W("WS-DAYNUM"))
        subtract(1, W("WS-DAYNUM"))
        check_leap()
        if W("WS-LEAP").text == "Y" and W("WS-MM").value > 2:
            add(1, W("WS-DAYNUM"))

    def num_to_date():
        move(W("WS-DAYNUM"), W("WS-TRY"))
        divide_giving(W("WS-DAYNUM"), 366, W("WS-Y"))
        compute(W("WS-YYYY"), dec(W("WS-Y")) + dec(1601))
        move(1, W("WS-MM"), W("WS-DD"))
        move("N", W("WS-DONE"))
        while W("WS-DONE").text != "Y":
            if W("WS-YYYY").value == 9999:
                move("Y", W("WS-DONE"))
            else:
                add(1, W("WS-YYYY"))
                date_to_num()
                if W("WS-DAYNUM").value > W("WS-TRY").value:
                    subtract(1, W("WS-YYYY"))
                    move("Y", W("WS-DONE"))
        move(12, W("WS-MM"))
        date_to_num()
        while not (W("WS-DAYNUM").value <= W("WS-TRY").value):
            subtract(1, W("WS-MM"))
            date_to_num()
        compute(W("WS-DD"), dec(W("WS-TRY")) - dec(W("WS-DAYNUM")) + dec(1))

    def do_pair():
        move(rec["DT-FROM"], W("WS-DATE"))
        validate_date()
        if W("WS-VALID").text == "N":
            out.extend(display_line(rec["DT-FROM"], " INVALID FROM DATE"))
            return
        date_to_num()
        move(W("WS-DAYNUM"), W("WS-FROM-NUM"))
        move(rec["DT-TO"], W("WS-DATE"))
        validate_date()
        if W("WS-VALID").text == "N":
            out.extend(display_line(rec["DT-TO"], " INVALID TO DATE"))
            return
        date_to_num()
        move(W("WS-DAYNUM"), W("WS-TO-NUM"))
        compute(W("WS-DIFF"), dec(W("WS-TO-NUM")) - dec(W("WS-FROM-NUM")))
        move(W("WS-DIFF"), W("WS-DIFF-ED"))
        divide_remainder(W("WS-FROM-NUM"), 7, W("WS-Q"), W("WS-REM7"))
        compute(W("WS-DOW-IX"), dec(W("WS-REM7")) + dec(1))
        compute(W("WS-NEW-NUM"), dec(W("WS-FROM-NUM")) + dec(rec["DT-OFFSET"]))
        nn = W("WS-NEW-NUM").value
        if nn < 0 or nn > 3067670:
            move("RANGE", W("WS-RESULT"))
        else:
            move(W("WS-NEW-NUM"), W("WS-DAYNUM"))
            num_to_date()
            move(W("WS-DATE"), W("WS-RESULT"))
        out.extend(display_line(rec["DT-FROM"], " ", rec["DT-TO"], " ", W("WS-DIFF-ED"), " ",
                                ws.f("WS-DOW-NAME", int(W("WS-DOW-IX"))), " ", W("WS-RESULT")))

    reader = LineSequentialReader(input_files.get("DATES.DAT", b""), 22)
    while W("WS-EOF").text != "Y":
        r = reader.read(rec.record())
        if r is None:
            move("Y", W("WS-EOF"))
        else:
            do_pair()

    return bytes(out), {}

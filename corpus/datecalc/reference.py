"""Reference Python translation of corpus/datecalc/program.cob (MIT licensed)."""

from cobol_equiv.runtime import (Alnum, Edited, Group, Num, Storage, add, compute, dec,
                                 display_line, divide_giving, divide_remainder, move, subtract)
from cobol_equiv.runtime.files import LineSequentialReader

DATE_REC = [Num("DT-FROM", "9(8)"), Num("DT-TO", "9(8)"), Num("DT-OFFSET", "S9(6)")]
MAX_DAYNUM = 3067670


def working_storage():
    return Storage("WS", [
        Alnum("WS-CUM-TEXT", "X(36)", value="000031059090120151181212243273304334"),
        Group("WS-CUM-TABLE", [Num("WS-CUM", "999", occurs=12)], redefines="WS-CUM-TEXT"),
        Alnum("WS-DIM-TEXT", "X(24)", value="312831303130313130313031"),
        Group("WS-DIM-TABLE", [Num("WS-DIM", "99", occurs=12)], redefines="WS-DIM-TEXT"),
        Alnum("WS-DOW-TEXT", "X(21)", value="MONTUEWEDTHUFRISATSUN"),
        Group("WS-DOW-TABLE", [Alnum("WS-DOW-NAME", "X(3)", occurs=7)], redefines="WS-DOW-TEXT"),
        Num("WS-DATE", "9(8)"),
        Group("WS-DATE-R", [Num("WS-YYYY", "9(4)"), Num("WS-MM", "99"), Num("WS-DD", "99")],
              redefines="WS-DATE"),
        Alnum("WS-VALID", "X"), Alnum("WS-LEAP", "X"),
        Num("WS-Q", "9(7)"), Num("WS-R4", "9(4)"), Num("WS-R100", "9(4)"), Num("WS-R400", "9(4)"),
        Num("WS-Y", "9(5)"),
        Num("WS-DAYNUM", "S9(8)"), Num("WS-FROM-NUM", "S9(8)"), Num("WS-TO-NUM", "S9(8)"),
        Num("WS-NEW-NUM", "S9(8)"), Num("WS-DIFF", "S9(8)"), Edited("WS-DIFF-ED", "-(7)9"),
        Num("WS-DOW-IX", "9"), Num("WS-REM7", "9"), Num("WS-MAXDAY", "99"),
        Alnum("WS-RESULT", "X(8)"), Num("WS-TRY", "S9(8)"), Alnum("WS-DONE", "X"),
    ])


class Program:
    def __init__(self):
        self.ws = working_storage()

    def v(self, name):
        return self.ws[name].value

    def check_leap(self):
        ws = self.ws
        divide_remainder(ws["WS-YYYY"], 4, ws["WS-Q"], ws["WS-R4"])
        divide_remainder(ws["WS-YYYY"], 100, ws["WS-Q"], ws["WS-R100"])
        divide_remainder(ws["WS-YYYY"], 400, ws["WS-Q"], ws["WS-R400"])
        leap = self.v("WS-R4") == 0 and (self.v("WS-R100") != 0 or self.v("WS-R400") == 0)
        move("Y" if leap else "N", ws["WS-LEAP"])

    def validate_date(self):
        ws = self.ws
        move("Y", ws["WS-VALID"])
        if self.v("WS-YYYY") < 1601 or self.v("WS-MM") < 1 or self.v("WS-MM") > 12 or self.v("WS-DD") < 1:
            move("N", ws["WS-VALID"])
        else:
            self.check_leap()
            move(ws.f("WS-DIM", int(self.v("WS-MM"))), ws["WS-MAXDAY"])
            if self.v("WS-MM") == 2 and ws["WS-LEAP"].raw == b"Y":
                add(1, ws["WS-MAXDAY"])
            if self.v("WS-DD") > self.v("WS-MAXDAY"):
                move("N", ws["WS-VALID"])

    def date_to_num(self):
        ws = self.ws
        compute(ws["WS-Y"], dec(ws["WS-YYYY"]) - 1601)
        divide_giving(ws["WS-Y"], 4, ws["WS-Q"])
        compute(ws["WS-DAYNUM"], dec(ws["WS-Y"]) * 365 + dec(ws["WS-Q"]))
        divide_giving(ws["WS-Y"], 100, ws["WS-Q"])
        subtract(ws["WS-Q"], ws["WS-DAYNUM"])
        divide_giving(ws["WS-Y"], 400, ws["WS-Q"])
        add(ws["WS-Q"], ws["WS-DAYNUM"])
        add([ws.f("WS-CUM", int(self.v("WS-MM"))), ws["WS-DD"]], ws["WS-DAYNUM"])
        subtract(1, ws["WS-DAYNUM"])
        self.check_leap()
        if ws["WS-LEAP"].raw == b"Y" and self.v("WS-MM") > 2:
            add(1, ws["WS-DAYNUM"])

    def num_to_date(self):
        ws = self.ws
        move(ws["WS-DAYNUM"], ws["WS-TRY"])
        divide_giving(ws["WS-DAYNUM"], 366, ws["WS-Y"])
        compute(ws["WS-YYYY"], dec(ws["WS-Y"]) + 1601)
        move(1, ws["WS-MM"], ws["WS-DD"])
        move("N", ws["WS-DONE"])
        while ws["WS-DONE"].raw != b"Y":
            if self.v("WS-YYYY") == 9999:
                move("Y", ws["WS-DONE"])
            else:
                add(1, ws["WS-YYYY"])
                self.date_to_num()
                if self.v("WS-DAYNUM") > self.v("WS-TRY"):
                    subtract(1, ws["WS-YYYY"])
                    move("Y", ws["WS-DONE"])
        move(12, ws["WS-MM"])
        self.date_to_num()
        while not self.v("WS-DAYNUM") <= self.v("WS-TRY"):
            subtract(1, ws["WS-MM"])
            self.date_to_num()
        compute(ws["WS-DD"], dec(ws["WS-TRY"]) - dec(ws["WS-DAYNUM"]) + 1)

    def do_pair(self, d, out):
        ws = self.ws
        move(d["DT-FROM"], ws["WS-DATE"])
        self.validate_date()
        if ws["WS-VALID"].raw == b"N":
            out += display_line(d["DT-FROM"], " INVALID FROM DATE")
            return
        self.date_to_num()
        move(ws["WS-DAYNUM"], ws["WS-FROM-NUM"])
        move(d["DT-TO"], ws["WS-DATE"])
        self.validate_date()
        if ws["WS-VALID"].raw == b"N":
            out += display_line(d["DT-TO"], " INVALID TO DATE")
            return
        self.date_to_num()
        move(ws["WS-DAYNUM"], ws["WS-TO-NUM"])
        compute(ws["WS-DIFF"], dec(ws["WS-TO-NUM"]) - dec(ws["WS-FROM-NUM"]))
        move(ws["WS-DIFF"], ws["WS-DIFF-ED"])
        divide_remainder(ws["WS-FROM-NUM"], 7, ws["WS-Q"], ws["WS-REM7"])
        compute(ws["WS-DOW-IX"], dec(ws["WS-REM7"]) + 1)
        compute(ws["WS-NEW-NUM"], dec(ws["WS-FROM-NUM"]) + dec(d["DT-OFFSET"]))
        if self.v("WS-NEW-NUM") < 0 or self.v("WS-NEW-NUM") > MAX_DAYNUM:
            move("RANGE", ws["WS-RESULT"])
        else:
            move(ws["WS-NEW-NUM"], ws["WS-DAYNUM"])
            self.num_to_date()
            move(ws["WS-DATE"], ws["WS-RESULT"])
        out += display_line(d["DT-FROM"], " ", d["DT-TO"], " ", ws["WS-DIFF-ED"], " ",
                            ws.f("WS-DOW-NAME", int(self.v("WS-DOW-IX"))), " ", ws["WS-RESULT"])


def main(stdin: bytes, input_files: dict) -> tuple:
    p = Program()
    d = Storage("DATE-REC", DATE_REC)
    reader = LineSequentialReader(input_files["DATES.DAT"], d.size)
    out = bytearray()
    while reader.read(d.record()) is not None:
        p.do_pair(d, out)
    return bytes(out), {}

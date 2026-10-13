"""Reference Python translation of corpus/ctlbreak/program.cob (MIT licensed)."""

from cobol_equiv.runtime import (SPACES, Alnum, Edited, Filler, Group, Num, Storage, add, move)
from cobol_equiv.runtime.files import LineSequentialReader, LineSequentialWriter

SALES_REC = [Alnum("SL-REGION", "X(2)"), Alnum("SL-BRANCH", "X(3)"), Num("SL-AMOUNT", "S9(5)V99")]


def working_storage():
    return Storage("WS", [
        Alnum("WS-FIRST", "X", value="Y"),
        Alnum("WS-PREV-REGION", "X(2)"),
        Alnum("WS-PREV-BRANCH", "X(3)"),
        Num("WS-BRANCH-TOT", "S9(7)V99"),
        Num("WS-BRANCH-CNT", "9(4)"),
        Num("WS-REGION-TOT", "S9(8)V99"),
        Num("WS-GRAND-TOT", "S9(9)V99", value=0),
        Num("WS-GRAND-CNT", "9(5)", value=0),
        Group("BRANCH-LINE", [
            Filler("X(4)", SPACES), Alnum("BL-REGION", "X(2)"), Filler("X", "/"),
            Alnum("BL-BRANCH", "X(3)"), Filler("X", " "), Edited("BL-COUNT", "ZZZ9"), Filler("X", " "),
            Edited("BL-TOTAL", "Z,ZZZ,ZZ9.99CR"),
        ]),
        Group("REGION-LINE", [
            Filler("X(7)", "REGION "), Alnum("RL-REGION", "X(2)"), Filler("X(6)", " TOTAL"),
            Edited("RL-TOTAL", "---,---,--9.99"),
        ]),
        Group("GRAND-LINE", [
            Filler("X(6)", "GRAND "), Edited("GL-COUNT", "ZZ,ZZ9"), Filler("X", " "),
            Edited("GL-TOTAL", "$$$$,$$$,$$9.99-"),
        ]),
    ])


class Program:
    def __init__(self, files):
        self.ws = working_storage()
        self.sl = Storage("SALES-REC", SALES_REC)
        self.rpt = Storage("REPORT", [Alnum("REPORT-LINE", "X(40)")])
        self.reader = LineSequentialReader(files["SALES.DAT"], self.sl.size)
        self.writer = LineSequentialWriter()

    def write_from(self, group):
        move(self.ws[group], self.rpt["REPORT-LINE"])
        self.writer.write(self.rpt["REPORT-LINE"])

    def run(self):
        ws, sl = self.ws, self.sl
        while self.reader.read(sl.record()) is not None:
            self.process_sale()
        if ws["WS-FIRST"].raw == b"Y":
            move("NO DATA", self.rpt["REPORT-LINE"])
            self.writer.write(self.rpt["REPORT-LINE"])
        else:
            self.branch_break()
            self.region_break()
        move(ws["WS-GRAND-CNT"], ws["GL-COUNT"])
        move(ws["WS-GRAND-TOT"], ws["GL-TOTAL"])
        self.write_from("GRAND-LINE")

    def process_sale(self):
        ws, sl = self.ws, self.sl
        if ws["WS-FIRST"].raw == b"Y":
            move("N", ws["WS-FIRST"])
            move(sl["SL-REGION"], ws["WS-PREV-REGION"])
            move(sl["SL-BRANCH"], ws["WS-PREV-BRANCH"])
            move(0, ws["WS-BRANCH-TOT"], ws["WS-BRANCH-CNT"], ws["WS-REGION-TOT"])
        elif sl["SL-REGION"].raw != ws["WS-PREV-REGION"].raw:
            self.branch_break()
            self.region_break()
        elif sl["SL-BRANCH"].raw != ws["WS-PREV-BRANCH"].raw:
            self.branch_break()
        add(sl["SL-AMOUNT"], ws["WS-BRANCH-TOT"])
        add(1, [ws["WS-BRANCH-CNT"], ws["WS-GRAND-CNT"]])

    def branch_break(self):
        ws = self.ws
        move(ws["WS-PREV-REGION"], ws["BL-REGION"])
        move(ws["WS-PREV-BRANCH"], ws["BL-BRANCH"])
        move(ws["WS-BRANCH-CNT"], ws["BL-COUNT"])
        move(ws["WS-BRANCH-TOT"], ws["BL-TOTAL"])
        self.write_from("BRANCH-LINE")
        add(ws["WS-BRANCH-TOT"], ws["WS-REGION-TOT"])
        move(0, ws["WS-BRANCH-TOT"], ws["WS-BRANCH-CNT"])
        move(self.sl["SL-BRANCH"], ws["WS-PREV-BRANCH"])

    def region_break(self):
        ws = self.ws
        move(ws["WS-PREV-REGION"], ws["RL-REGION"])
        move(ws["WS-REGION-TOT"], ws["RL-TOTAL"])
        self.write_from("REGION-LINE")
        add(ws["WS-REGION-TOT"], ws["WS-GRAND-TOT"])
        move(0, ws["WS-REGION-TOT"])
        move(self.sl["SL-REGION"], ws["WS-PREV-REGION"])


def main(stdin: bytes, input_files: dict) -> tuple:
    p = Program(input_files)
    p.run()
    return b"", {"REPORT.DAT": p.writer.getvalue()}

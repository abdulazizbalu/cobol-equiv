"""Reference Python translation of benchmark/runner-test/tally/program.cob
(MIT licensed)."""

from cobol_equiv.runtime import Alnum, Edited, Num, Storage, add, display_line, move
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = Storage("WS", [Num("WS-COUNT", "9(3)", value=0), Num("WS-TOTAL", "9(5)V99", value=0),
                        Edited("WS-OUT", "ZZ,ZZ9.99")])
    rec = Storage("IN-REC", [Alnum("IN-CODE", "X"), Num("IN-AMT", "9(3)V99")])
    reader = LineSequentialReader(input_files["VALUES.DAT"], rec.size)
    while reader.read(rec.record()) is not None:
        if rec["IN-CODE"].raw == b"A":
            add(1, ws["WS-COUNT"])
            add(rec["IN-AMT"], ws["WS-TOTAL"])
    move(ws["WS-TOTAL"], ws["WS-OUT"])
    return display_line("COUNT ", ws["WS-COUNT"], " TOTAL ", ws["WS-OUT"]), {}

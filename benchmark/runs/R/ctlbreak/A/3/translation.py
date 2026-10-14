from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited, Filler, move, add,
)
from cobol_equiv.runtime.files import LineSequentialReader, LineSequentialWriter


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    sales = Storage("SALES-FILE", [
        Group("SALES-REC", [
            Alnum("SL-REGION", "X(2)"),
            Alnum("SL-BRANCH", "X(3)"),
            Num("SL-AMOUNT", "S9(5)V99"),
        ]),
    ])
    rpt = Storage("REPORT-FILE", [
        Alnum("REPORT-LINE", "X(40)"),
    ])
    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
        Alnum("WS-FIRST", "X", value="Y"),
        Alnum("WS-PREV-REGION", "X(2)"),
        Alnum("WS-PREV-BRANCH", "X(3)"),
        Num("WS-BRANCH-TOT", "S9(7)V99"),
        Num("WS-BRANCH-CNT", "9(4)"),
        Num("WS-REGION-TOT", "S9(8)V99"),
        Num("WS-GRAND-TOT", "S9(9)V99", value=0),
        Num("WS-GRAND-CNT", "9(5)", value=0),
        Group("BRANCH-LINE", [
            Filler("X(4)", " "),
            Alnum("BL-REGION", "X(2)"),
            Filler("X", "/"),
            Alnum("BL-BRANCH", "X(3)"),
            Filler("X", " "),
            Edited("BL-COUNT", "ZZZ9"),
            Filler("X", " "),
            Edited("BL-TOTAL", "Z,ZZZ,ZZ9.99CR"),
        ]),
        Group("REGION-LINE", [
            Filler("X(7)", "REGION "),
            Alnum("RL-REGION", "X(2)"),
            Filler("X(6)", " TOTAL"),
            Edited("RL-TOTAL", "---,---,--9.99"),
        ]),
        Group("GRAND-LINE", [
            Filler("X(6)", "GRAND "),
            Edited("GL-COUNT", "ZZ,ZZ9"),
            Filler("X", " "),
            Edited("GL-TOTAL", "$$$$,$$$,$$9.99-"),
        ]),
    ])

    reader = LineSequentialReader(input_files.get("SALES.DAT", b""), 12)
    writer = LineSequentialWriter()
    rec = sales["SALES-REC"]
    rline = rpt["REPORT-LINE"]

    def write_from(src):
        move(src, rline)
        writer.write(rline)

    def branch_break():
        move(ws["WS-PREV-REGION"], ws["BL-REGION"])
        move(ws["WS-PREV-BRANCH"], ws["BL-BRANCH"])
        move(ws["WS-BRANCH-CNT"], ws["BL-COUNT"])
        move(ws["WS-BRANCH-TOT"], ws["BL-TOTAL"])
        write_from(ws["BRANCH-LINE"])
        add(ws["WS-BRANCH-TOT"], ws["WS-REGION-TOT"])
        move(0, ws["WS-BRANCH-TOT"], ws["WS-BRANCH-CNT"])
        move(sales["SL-BRANCH"], ws["WS-PREV-BRANCH"])

    def region_break():
        move(ws["WS-PREV-REGION"], ws["RL-REGION"])
        move(ws["WS-REGION-TOT"], ws["RL-TOTAL"])
        write_from(ws["REGION-LINE"])
        add(ws["WS-REGION-TOT"], ws["WS-GRAND-TOT"])
        move(0, ws["WS-REGION-TOT"])
        move(sales["SL-REGION"], ws["WS-PREV-REGION"])

    def process_sale():
        if ws["WS-FIRST"].raw == b"Y":
            move("N", ws["WS-FIRST"])
            move(sales["SL-REGION"], ws["WS-PREV-REGION"])
            move(sales["SL-BRANCH"], ws["WS-PREV-BRANCH"])
            move(0, ws["WS-BRANCH-TOT"], ws["WS-BRANCH-CNT"], ws["WS-REGION-TOT"])
        else:
            if sales["SL-REGION"].raw != ws["WS-PREV-REGION"].raw:
                branch_break()
                region_break()
            elif sales["SL-BRANCH"].raw != ws["WS-PREV-BRANCH"].raw:
                branch_break()
        add(sales["SL-AMOUNT"], ws["WS-BRANCH-TOT"])
        add(1, [ws["WS-BRANCH-CNT"], ws["WS-GRAND-CNT"]])

    while ws["WS-EOF"].raw != b"Y":
        r = reader.read(rec)
        if r is None:
            move("Y", ws["WS-EOF"])
        else:
            process_sale()

    if ws["WS-FIRST"].raw == b"Y":
        move("NO DATA", rline)
        writer.write(rline)
    else:
        branch_break()
        region_break()

    move(ws["WS-GRAND-CNT"], ws["GL-COUNT"])
    move(ws["WS-GRAND-TOT"], ws["GL-TOTAL"])
    write_from(ws["GRAND-LINE"])

    return b"", {"REPORT.DAT": writer.getvalue()}

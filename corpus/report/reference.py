"""Reference Python translation of corpus/report/program.cob (MIT licensed)."""

from cobol_equiv.runtime import Alnum, Edited, Filler, Group, Num, Storage, add, move
from cobol_equiv.runtime.files import LineSequentialReader, LineSequentialWriter

AMT_REC = [Alnum("AM-LABEL", "X(6)"), Num("AM-VALUE", "S9(7)V99"), Num("AM-DATE", "9(6)"),
           Num("AM-QTY", "S9(4)")]


def working_storage():
    return Storage("WS", [
        Num("WS-TOTAL", "S9(9)V99", value=0),
        Num("WS-QTY-TOTAL", "S9(6)", value=0),
        Group("LINE-1", [
            Alnum("L1-LABEL", "X(6)"), Filler("X", " "),
            Edited("L1-A", "ZZZ,ZZ9.99-"), Filler("X", " "),
            Edited("L1-B", "$$$,$$$,$$9.99CR"), Filler("X", " "),
            Edited("L1-C", "***,***,**9.99"), Filler("X", " "),
            Edited("L1-D", "+ZZZ9"), Filler("X", " "),
            Edited("L1-E", "99/99/99"), Filler("X", " "),
            Edited("L1-F", "---,--9"),
        ]),
        Group("LINE-2", [
            Filler("X(7)", "       "),
            Edited("L2-G", "Z(4)9.999"), Filler("X", " "),
            Edited("L2-H", "999B999"), Filler("X", " "),
            Edited("L2-I", "$ZZ,ZZ9.99DB"), Filler("X", " "),
            Edited("L2-J", "ZZ9.9+"), Filler("X", " "),
            Edited("L2-K", "ZZZZ"),
        ]),
        Group("TOTAL-LINE", [
            Filler("X(7)", "TOTAL  "), Edited("TL-AMOUNT", "$$$$,$$$,$$9.99CR"),
            Filler("X(5)", " QTY "), Edited("TL-QTY", "---,--9"),
        ]),
    ])


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = working_storage()
    a = Storage("AMT-REC", AMT_REC)
    rpt = Storage("RPT", [Alnum("RPT-REC", "X(80)")])
    reader = LineSequentialReader(input_files["AMOUNTS.DAT"], a.size)
    writer = LineSequentialWriter()

    def write_from(name):
        move(ws[name], rpt["RPT-REC"])
        writer.write(rpt["RPT-REC"])

    while reader.read(a.record()) is not None:
        move(a["AM-LABEL"], ws["L1-LABEL"])
        move(a["AM-VALUE"], ws["L1-A"], ws["L1-B"], ws["L1-C"], ws["L2-G"], ws["L2-I"], ws["L2-J"])
        move(a["AM-QTY"], ws["L1-D"], ws["L1-F"], ws["L2-K"])
        move(a["AM-DATE"], ws["L1-E"], ws["L2-H"])
        write_from("LINE-1")
        write_from("LINE-2")
        add(a["AM-VALUE"], ws["WS-TOTAL"])
        add(a["AM-QTY"], ws["WS-QTY-TOTAL"])
    move(ws["WS-TOTAL"], ws["TL-AMOUNT"])
    move(ws["WS-QTY-TOTAL"], ws["TL-QTY"])
    write_from("TOTAL-LINE")
    return b"", {"REPORT.DAT": writer.getvalue()}

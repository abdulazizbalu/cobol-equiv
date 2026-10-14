from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited, Filler, move, add, SPACES,
)
from cobol_equiv.runtime.files import LineSequentialReader, LineSequentialWriter


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    amt = Storage("AMT-FILE", [
        Group("AMT-REC", [
            Alnum("AM-LABEL", "X(6)"),
            Num("AM-VALUE", "S9(7)V99"),
            Num("AM-DATE", "9(6)"),
            Num("AM-QTY", "S9(4)"),
        ]),
    ])
    rpt = Storage("RPT-FILE", [Alnum("RPT-REC", "X(80)")])

    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
        Num("WS-TOTAL", "S9(9)V99", value=0),
        Num("WS-QTY-TOTAL", "S9(6)", value=0),
    ])
    line1 = Storage("LINE-1", [
        Alnum("L1-LABEL", "X(6)"),
        Filler("X", SPACES),
        Edited("L1-A", "ZZZ,ZZ9.99-"),
        Filler("X", SPACES),
        Edited("L1-B", "$$$,$$$,$$9.99CR"),
        Filler("X", SPACES),
        Edited("L1-C", "***,***,**9.99"),
        Filler("X", SPACES),
        Edited("L1-D", "+ZZZ9"),
        Filler("X", SPACES),
        Edited("L1-E", "99/99/99"),
        Filler("X", SPACES),
        Edited("L1-F", "---,--9"),
    ])
    line2 = Storage("LINE-2", [
        Filler("X(7)", "       "),
        Edited("L2-G", "Z(4)9.999"),
        Filler("X", SPACES),
        Edited("L2-H", "999B999"),
        Filler("X", SPACES),
        Edited("L2-I", "$ZZ,ZZ9.99DB"),
        Filler("X", SPACES),
        Edited("L2-J", "ZZ9.9+"),
        Filler("X", SPACES),
        Edited("L2-K", "ZZZZ"),
    ])
    total_line = Storage("TOTAL-LINE", [
        Filler("X(7)", "TOTAL  "),
        Edited("TL-AMOUNT", "$$$$,$$$,$$9.99CR"),
        Filler("X(5)", " QTY "),
        Edited("TL-QTY", "---,--9"),
    ])

    reader = LineSequentialReader(input_files.get("AMOUNTS.DAT", b""), 25)
    writer = LineSequentialWriter()

    def write_from(src):
        move(src.record(), rpt["RPT-REC"])
        writer.write(rpt["RPT-REC"])

    rec = amt["AMT-REC"]
    while ws["WS-EOF"].text != "Y":
        r = reader.read(rec)
        if r is None:
            move("Y", ws["WS-EOF"])
        else:
            move(amt["AM-LABEL"], line1["L1-LABEL"])
            move(amt["AM-VALUE"], line1["L1-A"], line1["L1-B"], line1["L1-C"],
                 line2["L2-G"], line2["L2-I"], line2["L2-J"])
            move(amt["AM-QTY"], line1["L1-D"], line1["L1-F"], line2["L2-K"])
            move(amt["AM-DATE"], line1["L1-E"], line2["L2-H"])
            write_from(line1)
            write_from(line2)
            add(amt["AM-VALUE"], ws["WS-TOTAL"])
            add(amt["AM-QTY"], ws["WS-QTY-TOTAL"])

    move(ws["WS-TOTAL"], total_line["TL-AMOUNT"])
    move(ws["WS-QTY-TOTAL"], total_line["TL-QTY"])
    write_from(total_line)

    return b"", {"REPORT.DAT": writer.getvalue()}

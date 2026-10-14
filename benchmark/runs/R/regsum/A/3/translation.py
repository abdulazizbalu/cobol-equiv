from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited, Filler,
    move, add, initialize, string, display_line, dec,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    rec = Storage("SALES-REC", [
        Alnum("SL-REGION", "X(2)"),
        Num("SL-MONTH", "99"),
        Num("SL-AMOUNT", "S9(5)V99"),
    ])
    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
        Alnum("WS-FIRST", "X", value="Y"),
        Group("WS-REGION-SUM", [
            Alnum("RS-REGION", "X(2)"),
            Alnum("RS-NAME", "X(10)"),
            Group("RS-MONTHS", [
                Group("RS-MONTH", [
                    Num("RS-AMT", "S9(6)V99"),
                    Num("RS-CNT", "9(3)"),
                ], occurs=12),
            ]),
            Group("RS-TOTALS", [
                Num("RS-TOTAL", "S9(7)V99"),
                Num("RS-BEST", "99"),
                Edited("RS-SHOWN", "-(6)9.99"),
            ]),
        ]),
        Num("WS-M", "99"),
        Num("WS-REJECTS", "9(3)", value=0),
        Edited("WS-OUT-AMT", "-(6)9.99"),
    ])

    out = bytearray()

    def print_region():
        move(1, ws["RS-BEST"])
        move(1, ws["WS-M"])
        while not (int(ws["WS-M"]) > 12):
            m = int(ws["WS-M"])
            if int(ws.f("RS-CNT", m)) > 0:
                move(ws.f("RS-AMT", m), ws["WS-OUT-AMT"])
                out.extend(display_line(ws["RS-REGION"], " ", ws["WS-M"], " ",
                                        ws["WS-OUT-AMT"], " ", ws.f("RS-CNT", m)))
            best = int(ws["RS-BEST"])
            if ws.f("RS-AMT", m).value > ws.f("RS-AMT", best).value:
                move(ws["WS-M"], ws["RS-BEST"])
            add(1, ws["WS-M"])
        move(ws["RS-TOTAL"], ws["RS-SHOWN"])
        out.extend(display_line(ws["RS-NAME"], " TOTAL ", ws["RS-SHOWN"],
                                " BEST ", ws["RS-BEST"]))

    def add_sale():
        month = int(rec["SL-MONTH"])
        if month < 1 or month > 12:
            add(1, ws["WS-REJECTS"])
        else:
            if ws["WS-FIRST"].text == "N" and rec["SL-REGION"].raw != ws["RS-REGION"].raw:
                print_region()
                initialize(ws["WS-REGION-SUM"])
            move("N", ws["WS-FIRST"])
            move(rec["SL-REGION"], ws["RS-REGION"])
            string([("REGION ", None), (rec["SL-REGION"], None)], ws["RS-NAME"])
            add(rec["SL-AMOUNT"], [ws.f("RS-AMT", month), ws["RS-TOTAL"]])
            add(1, ws.f("RS-CNT", month))

    initialize(ws["WS-REGION-SUM"])
    reader = LineSequentialReader(input_files.get("SALES.DAT", b""), 11)
    while ws["WS-EOF"].text != "Y":
        r = reader.read(rec.record())
        if r is None:
            move("Y", ws["WS-EOF"])
        else:
            add_sale()
    if ws["WS-FIRST"].text == "N":
        print_region()
    out.extend(display_line("REJECTED ", ws["WS-REJECTS"]))
    return bytes(out), {}

"""Reference Python translation of benchmark/corpus-r/regsum/program.cob
(MIT licensed)."""

from cobol_equiv.runtime import (Alnum, Edited, Group, Num, Storage, add, display_line, initialize,
                                 move, string)
from cobol_equiv.runtime.files import LineSequentialReader

SALES_REC = [Alnum("SL-REGION", "X(2)"), Num("SL-MONTH", "99"), Num("SL-AMOUNT", "S9(5)V99")]


def working_storage():
    return Storage("WS", [
        Group("WS-REGION-SUM", [
            Alnum("RS-REGION", "X(2)"),
            Alnum("RS-NAME", "X(10)"),
            Group("RS-MONTHS", [
                Group("RS-MONTH", [Num("RS-AMT", "S9(6)V99"), Num("RS-CNT", "9(3)")], occurs=12),
            ]),
            Group("RS-TOTALS", [Num("RS-TOTAL", "S9(7)V99"), Num("RS-BEST", "99"),
                                Edited("RS-SHOWN", "-(6)9.99")]),
        ]),
        Num("WS-M", "99"),
        Num("WS-REJECTS", "9(3)", value=0),
        Edited("WS-OUT-AMT", "-(6)9.99"),
    ])


def print_region(ws, out):
    move(1, ws["RS-BEST"])
    for m in range(1, 13):
        move(m, ws["WS-M"])
        if ws.f("RS-CNT", m).value > 0:
            move(ws.f("RS-AMT", m), ws["WS-OUT-AMT"])
            out += display_line(ws["RS-REGION"], " ", ws["WS-M"], " ", ws["WS-OUT-AMT"], " ", ws.f("RS-CNT", m))
        if ws.f("RS-AMT", m).value > ws.f("RS-AMT", int(ws["RS-BEST"].value)).value:
            move(ws["WS-M"], ws["RS-BEST"])
    move(13, ws["WS-M"])
    move(ws["RS-TOTAL"], ws["RS-SHOWN"])
    out += display_line(ws["RS-NAME"], " TOTAL ", ws["RS-SHOWN"], " BEST ", ws["RS-BEST"])


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = working_storage()
    sl = Storage("SALES-REC", SALES_REC)
    reader = LineSequentialReader(input_files["SALES.DAT"], sl.size)
    out = bytearray()
    first = True
    initialize(ws["WS-REGION-SUM"])
    while reader.read(sl.record()) is not None:
        month = sl["SL-MONTH"].value
        if month < 1 or month > 12:
            add(1, ws["WS-REJECTS"])
            continue
        if not first and sl["SL-REGION"].raw != ws["RS-REGION"].raw:
            print_region(ws, out)
            initialize(ws["WS-REGION-SUM"])
        first = False
        move(sl["SL-REGION"], ws["RS-REGION"])
        string([("REGION ", None), (sl["SL-REGION"], None)], ws["RS-NAME"])
        m = int(month)
        add(sl["SL-AMOUNT"], [ws.f("RS-AMT", m), ws["RS-TOTAL"]])
        add(1, ws.f("RS-CNT", m))
    if not first:
        print_region(ws, out)
    out += display_line("REJECTED ", ws["WS-REJECTS"])
    return bytes(out), {}

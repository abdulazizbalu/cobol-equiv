"""Reference Python translation of benchmark/corpus-r/stockupd/program.cob
(MIT licensed)."""

from cobol_equiv.runtime import (All, Alnum, Group, Num, Storage, add, compute, dec, display_line,
                                 initialize, move, subtract)
from cobol_equiv.runtime.files import LineSequentialReader

TRAN_REC = [Num("TR-PART", "9(4)"), Alnum("TR-CODE", "X"), Num("TR-QTY", "9(3)")]
PARTS = ["1010BOLT   0500", "1020NUT    0300", "1110WASHER 0050", "2005GEAR   0010",
         "2500SHAFT  0000", "3300SPRING 0120", "4001PULLEY 0007", "7777BELT   0999"]
SIZE = len(PARTS)


def working_storage():
    return Storage("WS", [
        Group("PART-DATA", [Alnum(f"PART-{i}", "X(15)", value=v) for i, v in enumerate(PARTS, 1)]),
        Group("PART-TABLE", [
            Group("PT-ENTRY", [Num("PT-PART", "9(4)"), Alnum("PT-NAME", "X(7)"), Num("PT-ONHAND", "9(4)")],
                  occurs=SIZE),
        ], redefines="PART-DATA"),
        Group("WS-SUMMARY", [
            Group("SM-COUNTS", [Num("SM-RECEIPTS", "9(3)"), Num("SM-ISSUES", "9(3)"),
                                Num("SM-ADJUSTS", "9(3)"), Num("SM-ERRORS", "9(3)")]),
            Group("SM-QTY", [Num("SM-IN", "9(6)"), Num("SM-OUT", "9(6)"), Num("SM-SHORT", "9(6)")]),
            Alnum("SM-LAST-PART", "X(4)"),
        ]),
        Alnum("WS-STATUS", "X"),
        Num("WS-SHORT", "9(3)"),
    ])


def search_all(ws, part) -> int:
    lo, hi = 1, SIZE
    while lo <= hi:
        mid = (lo + hi) // 2
        k = ws.f("PT-PART", mid).value
        if k == part:
            return mid
        if k < part:
            lo = mid + 1
        else:
            hi = mid - 1
    return 0


def issue_stock(tr, ws, px, out):
    onhand = ws.f("PT-ONHAND", px)
    if tr["TR-QTY"].value > onhand.value:
        compute(ws["WS-SHORT"], dec(tr["TR-QTY"]) - dec(onhand))
        add(ws["WS-SHORT"], ws["SM-SHORT"])
        add(onhand, ws["SM-OUT"])
        move(0, onhand)
        out += display_line("SHORT ", tr["TR-PART"], " ", ws["WS-SHORT"])
    else:
        subtract(tr["TR-QTY"], onhand)
        add(tr["TR-QTY"], ws["SM-OUT"])


def apply_tran(tr, ws, out):
    px = search_all(ws, tr["TR-PART"].value)
    if px == 0:
        add(1, ws["SM-ERRORS"])
        out += display_line("UNKNOWN PART ", tr["TR-PART"])
        return  # EXIT SECTION
    move(tr["TR-PART"], ws["SM-LAST-PART"])
    code = tr["TR-CODE"].raw
    onhand = ws.f("PT-ONHAND", px)
    if code == b"R":
        add(1, ws["SM-RECEIPTS"])
        add(tr["TR-QTY"], [onhand, ws["SM-IN"]])
        if 500 <= tr["TR-QTY"].value <= 999:
            out += display_line("BULK RECEIPT ", tr["TR-PART"], " ", tr["TR-QTY"])
    elif code == b"I":
        add(1, ws["SM-ISSUES"])
        issue_stock(tr, ws, px, out)
    elif code in (b"+", b"-"):
        add(1, ws["SM-ADJUSTS"])
        if code == b"+":
            add(tr["TR-QTY"], onhand)
        elif tr["TR-QTY"].value > onhand.value:
            move(0, onhand)
        else:
            subtract(tr["TR-QTY"], onhand)
    else:
        add(1, ws["SM-ERRORS"])
        out += display_line("BAD CODE ", tr["TR-PART"], " [", tr["TR-CODE"], "]")


def print_stock(ws, out):
    for px in range(1, SIZE + 1):
        onhand = ws.f("PT-ONHAND", px).value
        move("E" if onhand == 0 else "L" if onhand < 20 else "O", ws["WS-STATUS"])
        out += display_line(ws.f("PT-PART", px), " ", ws.f("PT-NAME", px), " ", ws.f("PT-ONHAND", px), " ",
                            ws["WS-STATUS"])
    out += display_line("R ", ws["SM-RECEIPTS"], " I ", ws["SM-ISSUES"], " A ", ws["SM-ADJUSTS"], " E ",
                        ws["SM-ERRORS"])
    out += display_line("IN ", ws["SM-IN"], " OUT ", ws["SM-OUT"], " SHORT ", ws["SM-SHORT"], " LAST [",
                        ws["SM-LAST-PART"], "]")


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = working_storage()
    tr = Storage("TRAN-REC", TRAN_REC)
    move(All("X"), ws["WS-SUMMARY"])
    initialize(ws["WS-SUMMARY"])
    reader = LineSequentialReader(input_files["TRANS.DAT"], tr.size)
    out = bytearray()
    while reader.read(tr.record()) is not None:
        apply_tran(tr, ws, out)
    print_stock(ws, out)
    return bytes(out), {}

from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Filler, move, initialize, add, subtract,
    compute, dec, display_line, All,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()

    tran = Storage("TRAN-REC", [
        Num("TR-PART", "9(4)"),
        Alnum("TR-CODE", "X"),
        Num("TR-QTY", "9(3)"),
    ])

    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
        Group("PART-DATA", [
            Filler("X(15)", "1010BOLT   0500"),
            Filler("X(15)", "1020NUT    0300"),
            Filler("X(15)", "1110WASHER 0050"),
            Filler("X(15)", "2005GEAR   0010"),
            Filler("X(15)", "2500SHAFT  0000"),
            Filler("X(15)", "3300SPRING 0120"),
            Filler("X(15)", "4001PULLEY 0007"),
            Filler("X(15)", "7777BELT   0999"),
        ]),
        Group("PART-TABLE", [
            Group("PT-ENTRY", [
                Num("PT-PART", "9(4)"),
                Alnum("PT-NAME", "X(7)"),
                Num("PT-ONHAND", "9(4)"),
            ], occurs=8),
        ], redefines="PART-DATA"),
        Group("WS-SUMMARY", [
            Group("SM-COUNTS", [
                Num("SM-RECEIPTS", "9(3)"),
                Num("SM-ISSUES", "9(3)"),
                Num("SM-ADJUSTS", "9(3)"),
                Num("SM-ERRORS", "9(3)"),
            ]),
            Group("SM-QTY", [
                Num("SM-IN", "9(6)"),
                Num("SM-OUT", "9(6)"),
                Num("SM-SHORT", "9(6)"),
            ]),
            Alnum("SM-LAST-PART", "X(4)"),
        ]),
        Alnum("WS-STATUS", "X"),
        Num("WS-SHORT", "9(3)"),
    ])

    TR_PART = tran["TR-PART"]
    TR_CODE = tran["TR-CODE"]
    TR_QTY = tran["TR-QTY"]

    def onhand(px):
        return ws.f("PT-ONHAND", px)

    def issue_stock(px):
        if TR_QTY.value > onhand(px).value:
            compute(ws["WS-SHORT"], dec(TR_QTY) - dec(onhand(px)))
            add(ws["WS-SHORT"], ws["SM-SHORT"])
            add(onhand(px), ws["SM-OUT"])
            move(0, onhand(px))
            out.extend(display_line("SHORT ", TR_PART, " ", ws["WS-SHORT"]))
        else:
            subtract(TR_QTY, onhand(px))
            add(TR_QTY, ws["SM-OUT"])

    def apply_tran():
        found = None
        key = TR_PART.value
        for i in range(1, 9):
            if ws.f("PT-PART", i).value == key:
                found = i
                break
        if found is None:
            add(1, ws["SM-ERRORS"])
            out.extend(display_line("UNKNOWN PART ", TR_PART))
            return
        px = found
        move(TR_PART, ws["SM-LAST-PART"])
        code = TR_CODE.raw
        if code == b"R":
            add(1, ws["SM-RECEIPTS"])
            add(TR_QTY, [onhand(px), ws["SM-IN"]])
            q = TR_QTY.value
            if 500 <= q <= 999:
                out.extend(display_line("BULK RECEIPT ", TR_PART, " ", TR_QTY))
        elif code == b"I":
            add(1, ws["SM-ISSUES"])
            issue_stock(px)
        elif code in (b"+", b"-"):
            add(1, ws["SM-ADJUSTS"])
            if code == b"+":
                add(TR_QTY, onhand(px))
            else:
                if TR_QTY.value > onhand(px).value:
                    move(0, onhand(px))
                else:
                    subtract(TR_QTY, onhand(px))
        else:
            add(1, ws["SM-ERRORS"])
            out.extend(display_line("BAD CODE ", TR_PART, " [", TR_CODE, "]"))

    move(All("X"), ws["WS-SUMMARY"])
    initialize(ws["WS-SUMMARY"])

    reader = LineSequentialReader(input_files.get("TRANS.DAT", b""), 8)
    while True:
        r = reader.read(tran.record())
        if r is None:
            move("Y", ws["WS-EOF"])
            break
        apply_tran()

    for px in range(1, 9):
        v = onhand(px).value
        if v == 0:
            move("E", ws["WS-STATUS"])
        elif v < 20:
            move("L", ws["WS-STATUS"])
        else:
            move("O", ws["WS-STATUS"])
        out.extend(display_line(ws.f("PT-PART", px), " ", ws.f("PT-NAME", px), " ",
                                onhand(px), " ", ws["WS-STATUS"]))
    out.extend(display_line("R ", ws["SM-RECEIPTS"], " I ", ws["SM-ISSUES"],
                            " A ", ws["SM-ADJUSTS"], " E ", ws["SM-ERRORS"]))
    out.extend(display_line("IN ", ws["SM-IN"], " OUT ", ws["SM-OUT"],
                            " SHORT ", ws["SM-SHORT"], " LAST [", ws["SM-LAST-PART"], "]"))
    return bytes(out), {}

from decimal import Decimal

from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited, Filler,
    move, add, display_line, SPACES,
)
from cobol_equiv.runtime.files import LineSequentialReader, LineSequentialWriter


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()

    cust = Storage("CUST-REC", [
        Group("CUST-REC", [
            Num("CU-ID", "9(5)"),
            Group("CU-NAME", [
                Alnum("CU-LAST", "X(10)"),
                Alnum("CU-FIRST", "X(8)"),
            ]),
            Group("CU-ADDR", [
                Group("CU-STREET", [
                    Num("CU-HOUSE", "9(4)"),
                    Alnum("CU-ROAD", "X(12)"),
                ]),
                Alnum("CU-CITY", "X(10)"),
            ]),
            Group("CU-OPENED", [
                Num("CU-YYYY", "9(4)"),
                Num("CU-MM", "99"),
                Num("CU-DD", "99"),
            ]),
            Num("CU-OPENED-N", "9(8)", redefines="CU-OPENED"),
            Num("CU-BAL", "S9(5)V99"),
        ]),
    ])

    lst = Storage("LIST-REC", [Alnum("LIST-REC", "X(80)")])

    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
        Num("WS-COUNT", "9(3)", value=0),
        Num("WS-TOTAL", "S9(7)V99", value=0),
        Edited("WS-OUT-TOTAL", "-(7)9.99"),
        Alnum("WS-NAME-COPY", "X(20)"),
    ])

    wo = Storage("WS-OUT", [
        Group("WS-OUT", [
            Edited("CU-ID", "Z(4)9"),
            Filler("X", "|"),
            Group("CU-NAME", [
                Alnum("CU-FIRST", "X(8)"),
                Filler("X", " "),
                Alnum("CU-LAST", "X(10)"),
            ]),
            Filler("X", "|"),
            Group("CU-ADDR", [
                Alnum("CU-CITY", "X(10)"),
                Filler("X", ","),
                Group("CU-STREET", [
                    Edited("CU-HOUSE", "ZZZ9"),
                    Filler("X", " "),
                    Alnum("CU-ROAD", "X(12)"),
                ]),
            ]),
            Filler("X", "|"),
            Group("WO-DATE", [
                Num("WO-DD", "99"),
                Filler("X", "/"),
                Num("WO-MM", "99"),
                Filler("X", "/"),
                Num("WO-YYYY", "9(4)"),
            ]),
            Filler("X", "|"),
            Edited("CU-BAL", "-(5)9.99"),
            Alnum("WO-FLAG", "X(5)"),
        ]),
    ])

    reader = LineSequentialReader(input_files.get("CUST.DAT", b""), 64)
    writer = LineSequentialWriter()

    def list_customer():
        add(1, ws["WS-COUNT"])
        add(cust["CU-BAL"], ws["WS-TOTAL"])
        # MOVE CORRESPONDING
        move(cust["CU-ID"], wo["CU-ID"])
        move(cust["CU-LAST"], wo["CU-LAST"])
        move(cust["CU-FIRST"], wo["CU-FIRST"])
        move(cust["CU-HOUSE"], wo["CU-HOUSE"])
        move(cust["CU-ROAD"], wo["CU-ROAD"])
        move(cust["CU-CITY"], wo["CU-CITY"])
        move(cust["CU-BAL"], wo["CU-BAL"])
        move(cust["CU-DD"], wo["WO-DD"])
        move(cust["CU-MM"], wo["WO-MM"])
        move(cust["CU-YYYY"], wo["WO-YYYY"])
        mm = cust["CU-MM"].value
        if mm < Decimal(1) or mm > Decimal(12):
            move(" BADM", wo["WO-FLAG"])
        elif cust["CU-OPENED-N"].value < Decimal(19000101):
            move(" OLD", wo["WO-FLAG"])
        else:
            move(SPACES, wo["WO-FLAG"])
        move(wo["WS-OUT"], lst["LIST-REC"])
        writer.write(lst["LIST-REC"])
        if cust["CU-LAST"].raw == b" " * 10:
            move(cust["CU-NAME"], ws["WS-NAME-COPY"])
            out.extend(display_line("NO LAST NAME ", cust["CU-ID"], " [",
                                    ws["WS-NAME-COPY"], "]"))

    while ws["WS-EOF"].raw != b"Y":
        r = reader.read(cust.record())
        if r is None:
            move("Y", ws["WS-EOF"])
        else:
            list_customer()

    move(ws["WS-TOTAL"], ws["WS-OUT-TOTAL"])
    out.extend(display_line("COUNT ", ws["WS-COUNT"], " TOTAL ", ws["WS-OUT-TOTAL"]))
    return bytes(out), {"CUSTLIST.DAT": writer.getvalue()}

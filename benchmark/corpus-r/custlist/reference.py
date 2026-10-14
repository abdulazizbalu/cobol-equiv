"""Reference Python translation of benchmark/corpus-r/custlist/program.cob
(MIT licensed)."""

from cobol_equiv.runtime import (SPACES, Alnum, Edited, Filler, Group, Num, Storage, add,
                                 display_line, move)
from cobol_equiv.runtime.files import LineSequentialReader, LineSequentialWriter

CUST_REC = [
    Num("CU-ID", "9(5)"),
    Group("CU-NAME", [Alnum("CU-LAST", "X(10)"), Alnum("CU-FIRST", "X(8)")]),
    Group("CU-ADDR", [
        Group("CU-STREET", [Num("CU-HOUSE", "9(4)"), Alnum("CU-ROAD", "X(12)")]),
        Alnum("CU-CITY", "X(10)"),
    ]),
    Group("CU-OPENED", [Num("CU-YYYY", "9(4)"), Num("CU-MM", "99"), Num("CU-DD", "99")]),
    Num("CU-OPENED-N", "9(8)", redefines="CU-OPENED"),
    Num("CU-BAL", "S9(5)V99"),
]


def working_storage():
    return Storage("WS", [
        Num("WS-COUNT", "9(3)", value=0),
        Num("WS-TOTAL", "S9(7)V99", value=0),
        Edited("WS-OUT-TOTAL", "-(7)9.99"),
        Alnum("WS-NAME-COPY", "X(20)"),
        Group("WS-OUT", [
            Edited("CU-ID", "Z(4)9"), Filler("X", "|"),
            Group("CU-NAME", [Alnum("CU-FIRST", "X(8)"), Filler("X", " "), Alnum("CU-LAST", "X(10)")]),
            Filler("X", "|"),
            Group("CU-ADDR", [
                Alnum("CU-CITY", "X(10)"), Filler("X", ","),
                Group("CU-STREET", [Edited("CU-HOUSE", "ZZZ9"), Filler("X", " "), Alnum("CU-ROAD", "X(12)")]),
            ]),
            Filler("X", "|"),
            Group("WO-DATE", [Num("WO-DD", "99"), Filler("X", "/"), Num("WO-MM", "99"), Filler("X", "/"),
                              Num("WO-YYYY", "9(4)")]),
            Filler("X", "|"),
            Edited("CU-BAL", "-(5)9.99"),
            Alnum("WO-FLAG", "X(5)"),
        ]),
    ])


# MOVE CORRESPONDING CUST-REC TO WS-OUT: the elementary items with the same
# name and the same group names above them in both records.
CORRESPONDING = ["CU-ID", "CU-FIRST", "CU-LAST", "CU-CITY", "CU-HOUSE", "CU-ROAD", "CU-BAL"]


def list_customer(cu, ws, out, lst):
    add(1, ws["WS-COUNT"])
    add(cu["CU-BAL"], ws["WS-TOTAL"])
    for name in CORRESPONDING:
        move(cu[name], ws[name])
    move(cu["CU-DD"], ws["WO-DD"])
    move(cu["CU-MM"], ws["WO-MM"])
    move(cu["CU-YYYY"], ws["WO-YYYY"])
    mm = cu["CU-MM"].value
    if mm < 1 or mm > 12:
        move(" BADM", ws["WO-FLAG"])
    elif cu["CU-OPENED-N"].value < 19000101:
        move(" OLD", ws["WO-FLAG"])
    else:
        move(SPACES, ws["WO-FLAG"])
    lst.write(ws["WS-OUT"].raw.ljust(80))  # WRITE LIST-REC (X(80)) FROM WS-OUT
    if cu["CU-LAST"].raw.strip(b" ") == b"":
        move(cu["CU-NAME"], ws["WS-NAME-COPY"])
        out += display_line("NO LAST NAME ", cu["CU-ID"], " [", ws["WS-NAME-COPY"], "]")


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = working_storage()
    cu = Storage("CUST-REC", CUST_REC)
    reader = LineSequentialReader(input_files["CUST.DAT"], cu.size)
    lst = LineSequentialWriter()
    out = bytearray()
    while reader.read(cu.record()) is not None:
        list_customer(cu, ws, out, lst)
    move(ws["WS-TOTAL"], ws["WS-OUT-TOTAL"])
    out += display_line("COUNT ", ws["WS-COUNT"], " TOTAL ", ws["WS-OUT-TOTAL"])
    return bytes(out), {"CUSTLIST.DAT": lst.getvalue()}

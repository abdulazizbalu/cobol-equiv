"""Reference Python translation of corpus/classify/program.cob (MIT licensed)."""

from cobol_equiv.runtime import Alnum, Group, Num, Storage, add, display_line, move
from cobol_equiv.runtime.files import LineSequentialReader

CUST_REC = [Alnum("CU-ID", "X(4)"), Alnum("CU-TYPE", "X"), Num("CU-AGE", "9(3)"),
            Num("CU-BALANCE", "S9(7)V99"), Num("CU-DAYS-LATE", "9(3)")]


def working_storage():
    return Storage("WS", [
        Alnum("WS-CLASS", "X(7)"), Alnum("WS-SEGMENT", "X(10)"), Alnum("WS-AGEBAND", "X(6)"),
        Num("WS-RISK", "9"),
        Group("WS-COUNTS", [Num("WS-CNT-CREDIT", "9(3)", value=0), Num("WS-CNT-DEFAULT", "9(3)", value=0),
                            Num("WS-CNT-WATCH", "9(3)", value=0), Num("WS-CNT-NORMAL", "9(3)", value=0)]),
    ])


def classify_one(c, ws, out):
    bal = c["CU-BALANCE"].value
    late = c["CU-DAYS-LATE"].value
    age = c["CU-AGE"].value
    typ = c["CU-TYPE"].raw
    if bal < 0:
        move("CREDIT", ws["WS-CLASS"]); add(1, ws["WS-CNT-CREDIT"])
    elif late > 90:
        move("DEFAULT", ws["WS-CLASS"]); add(1, ws["WS-CNT-DEFAULT"])
    elif late > 30 and bal > 1000:
        move("WATCH", ws["WS-CLASS"]); add(1, ws["WS-CNT-WATCH"])
    else:
        move("NORMAL", ws["WS-CLASS"]); add(1, ws["WS-CNT-NORMAL"])

    if typ == b"P" and age < 25:
        seg = "YOUNG-P"
    elif typ == b"P" and age >= 65:
        seg = "SENIOR-P"
    elif typ == b"P":
        seg = "PERSONAL"
    elif typ == b"B":
        seg = "BUSINESS"
    elif b"G" <= typ <= b"J":  # alphanumeric THRU: byte (ASCII) order
        seg = "PUBLIC"
    else:
        seg = "UNKNOWN"
    move(seg, ws["WS-SEGMENT"])

    if typ == b"B":
        if bal > 50000 or late > 60:
            move(3, ws["WS-RISK"])
        elif bal > 10000:
            move(2, ws["WS-RISK"])
        else:
            move(1, ws["WS-RISK"])
    elif late == 0 and not bal < 0:
        move(0, ws["WS-RISK"])
    elif late > 30 or bal < -500:
        move(2, ws["WS-RISK"])
    else:
        move(1, ws["WS-RISK"])

    if 0 <= age <= 17:
        move("MINOR", ws["WS-AGEBAND"])
    elif 18 <= age <= 64:
        move("ADULT", ws["WS-AGEBAND"])
    else:
        move("SENIOR", ws["WS-AGEBAND"])
    out += display_line(c["CU-ID"], " ", ws["WS-CLASS"], " ", ws["WS-SEGMENT"], " ", ws["WS-RISK"], " ",
                        ws["WS-AGEBAND"])


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = working_storage()
    c = Storage("CUST-REC", CUST_REC)
    reader = LineSequentialReader(input_files["CUST.DAT"], c.size)
    out = bytearray()
    while reader.read(c.record()) is not None:
        classify_one(c, ws, out)
    out += display_line("CREDIT ", ws["WS-CNT-CREDIT"], " DEFAULT ", ws["WS-CNT-DEFAULT"],
                        " WATCH ", ws["WS-CNT-WATCH"], " NORMAL ", ws["WS-CNT-NORMAL"])
    return bytes(out), {}

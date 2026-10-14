from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, move, add, display_line,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()

    rec = Storage("CUST-REC", [
        Group("CUST-REC", [
            Alnum("CU-ID", "X(4)"),
            Alnum("CU-TYPE", "X"),
            Num("CU-AGE", "9(3)"),
            Num("CU-BALANCE", "S9(7)V99"),
            Num("CU-DAYS-LATE", "9(3)"),
        ]),
    ])

    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
        Alnum("WS-CLASS", "X(7)"),
        Alnum("WS-SEGMENT", "X(10)"),
        Alnum("WS-AGEBAND", "X(6)"),
        Num("WS-RISK", "9"),
        Group("WS-COUNTS", [
            Num("WS-CNT-CREDIT", "9(3)", value=0),
            Num("WS-CNT-DEFAULT", "9(3)", value=0),
            Num("WS-CNT-WATCH", "9(3)", value=0),
            Num("WS-CNT-NORMAL", "9(3)", value=0),
        ]),
    ])

    cu_id = rec["CU-ID"]
    cu_type = rec["CU-TYPE"]
    cu_age = rec["CU-AGE"]
    cu_bal = rec["CU-BALANCE"]
    cu_days = rec["CU-DAYS-LATE"]

    def classify_one():
        bal = cu_bal.value
        days = cu_days.value
        age = cu_age.value
        t = cu_type.raw

        if bal < 0:
            move("CREDIT", ws["WS-CLASS"])
            add(1, ws["WS-CNT-CREDIT"])
        elif days > 90:
            move("DEFAULT", ws["WS-CLASS"])
            add(1, ws["WS-CNT-DEFAULT"])
        elif days > 30 and bal > 1000:
            move("WATCH", ws["WS-CLASS"])
            add(1, ws["WS-CNT-WATCH"])
        else:
            move("NORMAL", ws["WS-CLASS"])
            add(1, ws["WS-CNT-NORMAL"])

        if t == b"P" and age < 25:
            seg = "YOUNG-P"
        elif t == b"P" and age >= 65:
            seg = "SENIOR-P"
        elif t == b"P":
            seg = "PERSONAL"
        elif t == b"B":
            seg = "BUSINESS"
        elif b"G" <= t <= b"J":
            seg = "PUBLIC"
        else:
            seg = "UNKNOWN"
        move(seg, ws["WS-SEGMENT"])

        if t == b"B":
            if bal > 50000 or days > 60:
                risk = 3
            elif bal > 10000:
                risk = 2
            else:
                risk = 1
        else:
            if days == 0 and not bal < 0:
                risk = 0
            elif days > 30 or bal < -500:
                risk = 2
            else:
                risk = 1
        move(risk, ws["WS-RISK"])

        if 0 <= age <= 17:
            band = "MINOR"
        elif 18 <= age <= 64:
            band = "ADULT"
        else:
            band = "SENIOR"
        move(band, ws["WS-AGEBAND"])

        out.extend(display_line(cu_id, " ", ws["WS-CLASS"], " ", ws["WS-SEGMENT"],
                                " ", ws["WS-RISK"], " ", ws["WS-AGEBAND"]))

    reader = LineSequentialReader(input_files.get("CUST.DAT", b""), 20)
    record = rec.record()
    while ws["WS-EOF"].raw != b"Y":
        r = reader.read(record)
        if r is None:
            move("Y", ws["WS-EOF"])
        else:
            classify_one()

    out.extend(display_line("CREDIT ", ws["WS-CNT-CREDIT"], " DEFAULT ", ws["WS-CNT-DEFAULT"],
                            " WATCH ", ws["WS-CNT-WATCH"], " NORMAL ", ws["WS-CNT-NORMAL"]))
    return bytes(out), {}

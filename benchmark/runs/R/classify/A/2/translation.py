from cobol_equiv.runtime import Storage, Group, Num, Alnum, move, add, display_line
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()

    rec = Storage("CUST-REC", [
        Alnum("CU-ID", "X(4)"),
        Alnum("CU-TYPE", "X"),
        Num("CU-AGE", "9(3)"),
        Num("CU-BALANCE", "S9(7)V99"),
        Num("CU-DAYS-LATE", "9(3)"),
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

    reader = LineSequentialReader(input_files.get("CUST.DAT", b""), 20)

    def classify_one():
        bal = rec["CU-BALANCE"].value
        days = rec["CU-DAYS-LATE"].value
        age = rec["CU-AGE"].value
        ctype = rec["CU-TYPE"].raw

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

        if ctype == b"P" and age < 25:
            seg = "YOUNG-P"
        elif ctype == b"P" and age >= 65:
            seg = "SENIOR-P"
        elif ctype == b"P":
            seg = "PERSONAL"
        elif ctype == b"B":
            seg = "BUSINESS"
        elif b"G" <= ctype <= b"J":
            seg = "PUBLIC"
        else:
            seg = "UNKNOWN"
        move(seg, ws["WS-SEGMENT"])

        if ctype == b"B":
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

        out.extend(display_line(rec["CU-ID"], " ", ws["WS-CLASS"], " ",
                                ws["WS-SEGMENT"], " ", ws["WS-RISK"], " ",
                                ws["WS-AGEBAND"]))

    while ws["WS-EOF"].raw != b"Y":
        r = reader.read(rec.record())
        if r is None:
            move("Y", ws["WS-EOF"])
        else:
            classify_one()

    out.extend(display_line("CREDIT ", ws["WS-CNT-CREDIT"], " DEFAULT ",
                            ws["WS-CNT-DEFAULT"], " WATCH ", ws["WS-CNT-WATCH"],
                            " NORMAL ", ws["WS-CNT-NORMAL"]))
    return bytes(out), {}

from cobol_equiv.runtime import Storage, Group, Num, Alnum, move, add, dec, display_line
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

    reader = LineSequentialReader(input_files.get("CUST.DAT", b""), 20)
    record = rec.record()

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
            move("YOUNG-P", ws["WS-SEGMENT"])
        elif ctype == b"P" and age >= 65:
            move("SENIOR-P", ws["WS-SEGMENT"])
        elif ctype == b"P":
            move("PERSONAL", ws["WS-SEGMENT"])
        elif ctype == b"B":
            move("BUSINESS", ws["WS-SEGMENT"])
        elif b"G" <= ctype <= b"J":
            move("PUBLIC", ws["WS-SEGMENT"])
        else:
            move("UNKNOWN", ws["WS-SEGMENT"])

        if ctype == b"B":
            if bal > 50000 or days > 60:
                move(3, ws["WS-RISK"])
            elif bal > 10000:
                move(2, ws["WS-RISK"])
            else:
                move(1, ws["WS-RISK"])
        else:
            if days == 0 and not bal < 0:
                move(0, ws["WS-RISK"])
            elif days > 30 or bal < -500:
                move(2, ws["WS-RISK"])
            else:
                move(1, ws["WS-RISK"])

        if 0 <= age <= 17:
            move("MINOR", ws["WS-AGEBAND"])
        elif 18 <= age <= 64:
            move("ADULT", ws["WS-AGEBAND"])
        else:
            move("SENIOR", ws["WS-AGEBAND"])

        out.extend(display_line(rec["CU-ID"], " ", ws["WS-CLASS"], " ",
                                ws["WS-SEGMENT"], " ", ws["WS-RISK"], " ",
                                ws["WS-AGEBAND"]))

    while ws["WS-EOF"].raw != b"Y":
        r = reader.read(record)
        if r is None:
            move("Y", ws["WS-EOF"])
        else:
            classify_one()

    out.extend(display_line("CREDIT ", ws["WS-CNT-CREDIT"], " DEFAULT ",
                            ws["WS-CNT-DEFAULT"], " WATCH ", ws["WS-CNT-WATCH"],
                            " NORMAL ", ws["WS-CNT-NORMAL"]))
    return bytes(out), {}

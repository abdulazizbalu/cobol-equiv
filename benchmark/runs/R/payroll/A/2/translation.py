from decimal import Decimal

from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, COMP3, SPACES,
    move, add, compute, dec, display_line,
)
from cobol_equiv.runtime.files import LineSequentialReader, RecordSequentialWriter


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    emp = Storage("EMP-FILE", [
        Group("EMP-REC", [
            Alnum("EMP-ID", "X(5)"),
            Alnum("EMP-NAME", "X(10)"),
            Num("EMP-HOURS", "9(3)V9"),
            Num("EMP-RATE", "9(3)V99"),
            Alnum("EMP-DED-CODE", "X"),
            Num("EMP-ADJUST", "S9(5)V99"),
        ]),
    ])
    pay = Storage("PAY-FILE", [
        Group("PAY-REC", [
            Alnum("PAY-ID", "X(5)"),
            Num("PAY-GROSS", "S9(7)V99", usage=COMP3),
            Num("PAY-NET", "S9(7)V99", usage=COMP3),
            Num("PAY-NET-D", "S9(7)V99"),
            Alnum("PAY-FLAG", "X"),
        ]),
    ])
    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
        Num("WS-OT-HOURS", "S9(3)V9", usage=COMP3),
        Num("WS-GROSS", "S9(7)V99", usage=COMP3),
        Num("WS-TAX", "S9(7)V99", usage=COMP3),
        Num("WS-DED", "S9(5)V99", usage=COMP3),
        Num("WS-NET", "S9(7)V99", usage=COMP3),
        Num("WS-TOT-GROSS", "S9(9)V99", usage=COMP3, value=0),
        Num("WS-TOT-NET", "S9(9)V99", usage=COMP3, value=0),
        Num("WS-NEG-COUNT", "9(3)", usage=COMP3, value=0),
        Num("WS-EMP-COUNT", "9(3)", usage=COMP3, value=0),
    ])

    out = bytearray()
    reader = LineSequentialReader(input_files.get("EMPLOYEES.DAT", b""), 32)
    writer = RecordSequentialWriter()

    emp_rec = emp["EMP-REC"]
    pay_rec = pay["PAY-REC"]

    def pay_one():
        add(1, ws["WS-EMP-COUNT"])
        if emp["EMP-HOURS"].value > 40:
            compute(ws["WS-OT-HOURS"], dec(emp["EMP-HOURS"]) - dec(40))
            compute(ws["WS-GROSS"],
                    dec(40) * dec(emp["EMP-RATE"])
                    + dec(ws["WS-OT-HOURS"]) * dec(emp["EMP-RATE"]) * dec("1.5"),
                    rounded=True)
        else:
            move(0, ws["WS-OT-HOURS"])
            compute(ws["WS-GROSS"], dec(emp["EMP-HOURS"]) * dec(emp["EMP-RATE"]),
                    rounded=True)
        g = ws["WS-GROSS"].value
        if g <= 1000:
            compute(ws["WS-TAX"], dec(ws["WS-GROSS"]) * dec("0.10"), rounded=True)
        elif g <= 5000:
            compute(ws["WS-TAX"],
                    dec(100) + (dec(ws["WS-GROSS"]) - dec(1000)) * dec("0.25"),
                    rounded=True)
        else:
            compute(ws["WS-TAX"],
                    dec(1100) + (dec(ws["WS-GROSS"]) - dec(5000)) * dec("0.35"),
                    rounded=True)
        code = emp["EMP-DED-CODE"].raw
        if code == b"A":
            move(50, ws["WS-DED"])
        elif code == b"B":
            compute(ws["WS-DED"], dec(ws["WS-GROSS"]) * dec("0.045"), rounded=True)
        elif code == b"C":
            move(0, ws["WS-DED"])
        else:
            move(Decimal("25.50"), ws["WS-DED"])
        compute(ws["WS-NET"],
                dec(ws["WS-GROSS"]) - dec(ws["WS-TAX"]) - dec(ws["WS-DED"])
                + dec(emp["EMP-ADJUST"]))
        move(SPACES, pay["PAY-FLAG"])
        if ws["WS-NET"].value < 0:
            add(1, ws["WS-NEG-COUNT"])
            move("N", pay["PAY-FLAG"])
        add(ws["WS-GROSS"], ws["WS-TOT-GROSS"])
        add(ws["WS-NET"], ws["WS-TOT-NET"])
        move(emp["EMP-ID"], pay["PAY-ID"])
        move(ws["WS-GROSS"], pay["PAY-GROSS"])
        move(ws["WS-NET"], pay["PAY-NET"])
        move(ws["WS-NET"], pay["PAY-NET-D"])
        writer.write(pay_rec)
        out.extend(display_line(emp["EMP-ID"], " ", emp["EMP-NAME"], " ",
                                ws["WS-GROSS"], " ", ws["WS-TAX"], " ",
                                ws["WS-DED"], " ", ws["WS-NET"]))

    while ws["WS-EOF"].raw != b"Y":
        r = reader.read(emp_rec)
        if r is None:
            move("Y", ws["WS-EOF"])
        else:
            pay_one()

    out.extend(display_line("EMPLOYEES ", ws["WS-EMP-COUNT"]))
    out.extend(display_line("TOTAL GROSS ", ws["WS-TOT-GROSS"]))
    out.extend(display_line("TOTAL NET   ", ws["WS-TOT-NET"]))
    out.extend(display_line("NEGATIVE NET ", ws["WS-NEG-COUNT"]))

    return bytes(out), {"PAYOUT.DAT": writer.getvalue()}

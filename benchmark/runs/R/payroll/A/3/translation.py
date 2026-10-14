from decimal import Decimal

from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, COMP3, move, add, compute, dec,
    display_line, SPACES,
)
from cobol_equiv.runtime.files import LineSequentialReader, RecordSequentialWriter


def main(stdin: bytes, input_files: dict) -> tuple:
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
    emp_id = emp["EMP-ID"]
    emp_name = emp["EMP-NAME"]
    hours = emp["EMP-HOURS"]
    rate = emp["EMP-RATE"]
    dcode = emp["EMP-DED-CODE"]
    adjust = emp["EMP-ADJUST"]

    ot = ws["WS-OT-HOURS"]
    gross = ws["WS-GROSS"]
    tax = ws["WS-TAX"]
    ded = ws["WS-DED"]
    net = ws["WS-NET"]

    def pay_one():
        add(1, ws["WS-EMP-COUNT"])
        if dec(hours) > dec(40):
            compute(ot, dec(hours) - dec(40))
            compute(gross, dec(40) * dec(rate) + dec(ot) * dec(rate) * dec("1.5"),
                    rounded=True)
        else:
            move(0, ot)
            compute(gross, dec(hours) * dec(rate), rounded=True)
        if dec(gross) <= dec(1000):
            compute(tax, dec(gross) * dec("0.10"), rounded=True)
        elif dec(gross) <= dec(5000):
            compute(tax, dec(100) + (dec(gross) - dec(1000)) * dec("0.25"), rounded=True)
        else:
            compute(tax, dec(1100) + (dec(gross) - dec(5000)) * dec("0.35"), rounded=True)
        code = dcode.raw
        if code == b"A":
            move(50, ded)
        elif code == b"B":
            compute(ded, dec(gross) * dec("0.045"), rounded=True)
        elif code == b"C":
            move(0, ded)
        else:
            move(Decimal("25.50"), ded)
        compute(net, dec(gross) - dec(tax) - dec(ded) + dec(adjust))
        move(SPACES, pay["PAY-FLAG"])
        if dec(net) < dec(0):
            add(1, ws["WS-NEG-COUNT"])
            move("N", pay["PAY-FLAG"])
        add(gross, ws["WS-TOT-GROSS"])
        add(net, ws["WS-TOT-NET"])
        move(emp_id, pay["PAY-ID"])
        move(gross, pay["PAY-GROSS"])
        move(net, pay["PAY-NET"])
        move(net, pay["PAY-NET-D"])
        writer.write(pay["PAY-REC"])
        out.extend(display_line(emp_id, " ", emp_name, " ", gross, " ", tax, " ",
                                ded, " ", net))

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

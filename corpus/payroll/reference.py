"""Reference Python translation of corpus/payroll/program.cob (MIT licensed)."""

from decimal import Decimal

from cobol_equiv.runtime import (COMP3, Alnum, Num, Storage, add, compute, dec, display_line,
                                 move, subtract)
from cobol_equiv.runtime.files import LineSequentialReader, RecordSequentialWriter

EMP_REC = [
    Alnum("EMP-ID", "X(5)"), Alnum("EMP-NAME", "X(10)"), Num("EMP-HOURS", "9(3)V9"),
    Num("EMP-RATE", "9(3)V99"), Alnum("EMP-DED-CODE", "X"), Num("EMP-ADJUST", "S9(5)V99"),
]
PAY_REC = [
    Alnum("PAY-ID", "X(5)"), Num("PAY-GROSS", "S9(7)V99", usage=COMP3),
    Num("PAY-NET", "S9(7)V99", usage=COMP3), Num("PAY-NET-D", "S9(7)V99"), Alnum("PAY-FLAG", "X"),
]


def working_storage():
    return Storage("WS", [
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


def pay_one(e, ws, pay, out, payfile):
    add(1, ws["WS-EMP-COUNT"])
    if e["EMP-HOURS"].value > 40:
        compute(ws["WS-OT-HOURS"], dec(e["EMP-HOURS"]) - 40)
        compute(ws["WS-GROSS"], 40 * dec(e["EMP-RATE"])
                + dec(ws["WS-OT-HOURS"]) * dec(e["EMP-RATE"]) * dec("1.5"), rounded=True)
    else:
        move(0, ws["WS-OT-HOURS"])
        compute(ws["WS-GROSS"], dec(e["EMP-HOURS"]) * dec(e["EMP-RATE"]), rounded=True)
    gross = ws["WS-GROSS"].value
    if gross <= 1000:
        compute(ws["WS-TAX"], dec(ws["WS-GROSS"]) * dec("0.10"), rounded=True)
    elif gross <= 5000:
        compute(ws["WS-TAX"], 100 + (dec(ws["WS-GROSS"]) - 1000) * dec("0.25"), rounded=True)
    else:
        compute(ws["WS-TAX"], 1100 + (dec(ws["WS-GROSS"]) - 5000) * dec("0.35"), rounded=True)
    code = e["EMP-DED-CODE"].raw
    if code == b"A":
        move(50, ws["WS-DED"])
    elif code == b"B":
        compute(ws["WS-DED"], dec(ws["WS-GROSS"]) * dec("0.045"), rounded=True)
    elif code == b"C":
        move(0, ws["WS-DED"])
    else:
        move(Decimal("25.50"), ws["WS-DED"])
    compute(ws["WS-NET"], dec(ws["WS-GROSS"]) - dec(ws["WS-TAX"]) - dec(ws["WS-DED"])
            + dec(e["EMP-ADJUST"]))
    move(" ", pay["PAY-FLAG"])
    if ws["WS-NET"].value < 0:
        add(1, ws["WS-NEG-COUNT"])
        move("N", pay["PAY-FLAG"])
    add(ws["WS-GROSS"], ws["WS-TOT-GROSS"])
    add(ws["WS-NET"], ws["WS-TOT-NET"])
    move(e["EMP-ID"], pay["PAY-ID"])
    move(ws["WS-GROSS"], pay["PAY-GROSS"])
    move(ws["WS-NET"], pay["PAY-NET"])
    move(ws["WS-NET"], pay["PAY-NET-D"])
    payfile.write(pay.record())
    out += display_line(e["EMP-ID"], " ", e["EMP-NAME"], " ", ws["WS-GROSS"], " ", ws["WS-TAX"], " ",
                        ws["WS-DED"], " ", ws["WS-NET"])


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = working_storage()
    e = Storage("EMP-REC", EMP_REC)
    pay = Storage("PAY-REC", PAY_REC)
    reader = LineSequentialReader(input_files["EMPLOYEES.DAT"], e.size)
    payfile = RecordSequentialWriter()
    out = bytearray()
    while reader.read(e.record()) is not None:
        pay_one(e, ws, pay, out, payfile)
    out += display_line("EMPLOYEES ", ws["WS-EMP-COUNT"])
    out += display_line("TOTAL GROSS ", ws["WS-TOT-GROSS"])
    out += display_line("TOTAL NET   ", ws["WS-TOT-NET"])
    out += display_line("NEGATIVE NET ", ws["WS-NEG-COUNT"])
    return bytes(out), {"PAYOUT.DAT": payfile.getvalue()}

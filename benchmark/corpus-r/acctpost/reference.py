"""Reference Python translation of benchmark/corpus-r/acctpost/program.cob
(MIT licensed)."""

from cobol_equiv.runtime import (Alnum, Edited, Group, Num, Storage, add, compute, dec,
                                 display_line, move, subtract)
from cobol_equiv.runtime.files import LineSequentialReader

TXN_REC = [Alnum("TX-ACCT", "X(4)"), Num("TX-TYPE", "9"), Num("TX-AMT", "9(5)V99")]


def working_storage():
    return Storage("WS", [
        Group("WS-ACCOUNTS", [
            Group("WS-ACC", [Alnum("WS-ACC-ID", "X(4)"), Num("WS-BAL", "S9(7)V99"),
                             Num("WS-NTX", "9(3)")], occurs=5),
        ]),
        Num("WS-NACC", "9", value=0),
        Num("WS-I", "9"),
        Num("WS-K", "9"),
        Num("WS-FEE", "9(3)V99"),
        Num("WS-ERRORS", "9(3)", value=0),
        Alnum("WS-MSG", "X(20)"),
        Edited("WS-OUT-BAL", "-(7)9.99"),
        Edited("WS-OUT-AMT", "Z(4)9.99"),
    ])


def find_account(tx, ws):
    move(0, ws["WS-K"])
    move(1, ws["WS-I"])
    while not (ws["WS-I"].value > ws["WS-NACC"].value or ws["WS-K"].value > 0):
        if ws.f("WS-ACC-ID", int(ws["WS-I"].value)).raw == tx["TX-ACCT"].raw:
            move(ws["WS-I"], ws["WS-K"])
        add(1, ws["WS-I"])
    if ws["WS-K"].value == 0 and ws["WS-NACC"].value < 5:
        add(1, ws["WS-NACC"])
        move(ws["WS-NACC"], ws["WS-K"])
        k = int(ws["WS-K"].value)
        move(tx["TX-ACCT"], ws.f("WS-ACC-ID", k))
        move(0, ws.f("WS-BAL", k), ws.f("WS-NTX", k))


def post_txn(tx, ws, out):
    """PERFORM POST-TXN THRU POST-EXIT; each GO TO becomes the name of the
    paragraph to continue with."""
    para = "POST-TXN"
    while True:
        if para == "POST-TXN":
            if tx["TX-ACCT"].raw.strip(b" ") == b"":
                move("NO ACCOUNT", ws["WS-MSG"])
                para = "POST-ERROR"
                continue
            find_account(tx, ws)
            if ws["WS-K"].value == 0:
                move("TOO MANY ACCOUNTS", ws["WS-MSG"])
                para = "POST-ERROR"
                continue
            t = int(tx["TX-TYPE"].value)
            if t in (1, 2, 3):
                para = ("DO-DEPOSIT", "DO-WITHDRAW", "DO-FEE")[t - 1]
                continue
            move("BAD TYPE", ws["WS-MSG"])
            para = "POST-ERROR"
        elif para == "DO-DEPOSIT":
            add(tx["TX-AMT"], ws.f("WS-BAL", int(ws["WS-K"].value)))
            para = "POST-COUNT"
        elif para == "DO-WITHDRAW":
            k = int(ws["WS-K"].value)
            if tx["TX-AMT"].value > ws.f("WS-BAL", k).value:
                move("INSUFFICIENT FUNDS", ws["WS-MSG"])
                para = "POST-ERROR"
                continue
            subtract(tx["TX-AMT"], ws.f("WS-BAL", k))
            para = "POST-COUNT"
        elif para == "DO-FEE":
            compute(ws["WS-FEE"], dec(tx["TX-AMT"]) * dec("0.015") + dec("0.25"), rounded=True)
            subtract(ws["WS-FEE"], ws.f("WS-BAL", int(ws["WS-K"].value)))
            move(ws["WS-FEE"], ws["WS-OUT-AMT"])
            out += display_line("FEE ", tx["TX-ACCT"], " ", ws["WS-OUT-AMT"])
            para = "POST-COUNT"  # falls through
        elif para == "POST-COUNT":
            add(1, ws.f("WS-NTX", int(ws["WS-K"].value)))
            return
        elif para == "POST-ERROR":
            add(1, ws["WS-ERRORS"])
            move(tx["TX-AMT"], ws["WS-OUT-AMT"])
            out += display_line("REJECT ", tx["TX-ACCT"], " ", tx["TX-TYPE"], " ", ws["WS-OUT-AMT"], " ",
                                ws["WS-MSG"])
            return


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = working_storage()
    tx = Storage("TXN-REC", TXN_REC)
    reader = LineSequentialReader(input_files["TXNS.DAT"], tx.size)
    out = bytearray()
    while reader.read(tx.record()) is not None:
        post_txn(tx, ws, out)
    move(1, ws["WS-I"])
    while not ws["WS-I"].value > ws["WS-NACC"].value:
        i = int(ws["WS-I"].value)
        move(ws.f("WS-BAL", i), ws["WS-OUT-BAL"])
        out += display_line(ws.f("WS-ACC-ID", i), " ", ws["WS-OUT-BAL"], " ", ws.f("WS-NTX", i))
        add(1, ws["WS-I"])
    out += display_line("ERRORS ", ws["WS-ERRORS"])
    return bytes(out), {}

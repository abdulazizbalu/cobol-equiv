from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited,
    move, add, subtract, compute, dec, display_line, SPACES,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()

    tx = Storage("TXN-REC", [
        Alnum("TX-ACCT", "X(4)"),
        Num("TX-TYPE", "9"),
        Num("TX-AMT", "9(5)V99"),
    ])
    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
        Group("WS-ACCOUNTS", [
            Group("WS-ACC", [
                Alnum("WS-ACC-ID", "X(4)"),
                Num("WS-BAL", "S9(7)V99"),
                Num("WS-NTX", "9(3)"),
            ], occurs=5),
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

    def find_account():
        move(0, ws["WS-K"])
        move(1, ws["WS-I"])
        while not (int(ws["WS-I"]) > int(ws["WS-NACC"]) or int(ws["WS-K"]) > 0):
            i = int(ws["WS-I"])
            if ws.f("WS-ACC-ID", i).raw == tx["TX-ACCT"].raw:
                move(ws["WS-I"], ws["WS-K"])
            add(1, ws["WS-I"])
        if int(ws["WS-K"]) == 0 and int(ws["WS-NACC"]) < 5:
            add(1, ws["WS-NACC"])
            move(ws["WS-NACC"], ws["WS-K"])
            k = int(ws["WS-K"])
            move(tx["TX-ACCT"], ws.f("WS-ACC-ID", k))
            move(0, ws.f("WS-BAL", k), ws.f("WS-NTX", k))

    def post_error():
        add(1, ws["WS-ERRORS"])
        move(tx["TX-AMT"], ws["WS-OUT-AMT"])
        out.extend(display_line("REJECT ", tx["TX-ACCT"], " ", tx["TX-TYPE"], " ",
                                ws["WS-OUT-AMT"], " ", ws["WS-MSG"]))

    def post_count():
        k = int(ws["WS-K"])
        add(1, ws.f("WS-NTX", k))

    def post_txn():
        if tx["TX-ACCT"].raw == b" " * 4:
            move("NO ACCOUNT", ws["WS-MSG"])
            post_error()
            return
        find_account()
        if int(ws["WS-K"]) == 0:
            move("TOO MANY ACCOUNTS", ws["WS-MSG"])
            post_error()
            return
        t = int(tx["TX-TYPE"])
        k = int(ws["WS-K"])
        if t == 1:
            add(tx["TX-AMT"], ws.f("WS-BAL", k))
            post_count()
            return
        if t == 2:
            if tx["TX-AMT"].value > ws.f("WS-BAL", k).value:
                move("INSUFFICIENT FUNDS", ws["WS-MSG"])
                post_error()
                return
            subtract(tx["TX-AMT"], ws.f("WS-BAL", k))
            post_count()
            return
        if t == 3:
            compute(ws["WS-FEE"], dec(tx["TX-AMT"]) * dec("0.015") + dec("0.25"),
                    rounded=True)
            subtract(ws["WS-FEE"], ws.f("WS-BAL", k))
            move(ws["WS-FEE"], ws["WS-OUT-AMT"])
            out.extend(display_line("FEE ", tx["TX-ACCT"], " ", ws["WS-OUT-AMT"]))
            post_count()
            return
        move("BAD TYPE", ws["WS-MSG"])
        post_error()

    reader = LineSequentialReader(input_files.get("TXNS.DAT", b""), 12)
    while ws["WS-EOF"].raw != b"Y":
        r = reader.read(tx.record())
        if r is None:
            move("Y", ws["WS-EOF"])
        else:
            post_txn()

    move(1, ws["WS-I"])
    while not (int(ws["WS-I"]) > int(ws["WS-NACC"])):
        i = int(ws["WS-I"])
        move(ws.f("WS-BAL", i), ws["WS-OUT-BAL"])
        out.extend(display_line(ws.f("WS-ACC-ID", i), " ", ws["WS-OUT-BAL"], " ",
                                ws.f("WS-NTX", i)))
        add(1, ws["WS-I"])
    out.extend(display_line("ERRORS ", ws["WS-ERRORS"]))
    return bytes(out), {}

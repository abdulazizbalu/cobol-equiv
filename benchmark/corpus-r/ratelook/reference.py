"""Reference Python translation of benchmark/corpus-r/ratelook/program.cob
(MIT licensed)."""

from cobol_equiv.runtime import (Alnum, Edited, Group, Num, Storage, add, compute, dec,
                                 display_line, move)
from cobol_equiv.runtime.files import LineSequentialReader

SHIP_REC = [Alnum("SH-ZONE", "X(2)"), Alnum("SH-CLASS", "X"), Num("SH-WEIGHT", "9(3)V9"),
            Num("SH-QTY", "99")]
RATES = ["AAE0450001250", "AAS0300000800", "BKE0600001575", "BKS0420001010", "CNE0725002030",
         "CNS0510001333", "DEE0999002500", "DES0650001725", "FRE0880002200", "FRS0600001480",
         "UZE1200003125", "UZS0875002250"]
SIZE = len(RATES)


def working_storage():
    return Storage("WS", [
        Group("RATE-DATA", [Alnum(f"RATE-{i}", "X(13)", value=v) for i, v in enumerate(RATES, 1)]),
        Group("RATE-TABLE", [
            Group("RT-ENTRY", [Alnum("RT-ZONE", "X(2)"), Alnum("RT-CLASS", "X"), Num("RT-BASE", "9(3)V99"),
                               Num("RT-PER-KG", "9(3)V99")], occurs=SIZE),
        ], redefines="RATE-DATA"),
        Num("WS-CHARGE", "9(7)V99"),
        Num("WS-TOTAL", "9(8)V99", value=0),
        Num("WS-FOUND", "9(3)", value=0),
        Num("WS-MISSING", "9(3)", value=0),
        Edited("WS-OUT-CHARGE", "Z,ZZZ,ZZ9.99"),
        Edited("WS-OUT-TOTAL", "ZZ,ZZZ,ZZ9.99"),
    ])


def search_all(ws, sh) -> int:
    """SEARCH ALL RT-ENTRY (ascending on RT-ZONE, RT-CLASS): binary search,
    0 for AT END."""
    key = sh["SH-ZONE"].raw + sh["SH-CLASS"].raw
    lo, hi = 1, SIZE
    while lo <= hi:
        mid = (lo + hi) // 2
        k = ws.f("RT-ZONE", mid).raw + ws.f("RT-CLASS", mid).raw
        if k == key:
            return mid
        if k < key:
            lo = mid + 1
        else:
            hi = mid - 1
    return 0


def price_shipment(sh, ws, out):
    rx = search_all(ws, sh)
    if rx == 0:
        add(1, ws["WS-MISSING"])
        out += display_line("NO RATE ", sh["SH-ZONE"], "/", sh["SH-CLASS"])
        return
    add(1, ws["WS-FOUND"])
    qty = dec(sh["SH-QTY"])
    compute(ws["WS-CHARGE"],
            (dec(ws.f("RT-BASE", rx)) + dec(ws.f("RT-PER-KG", rx)) * dec(sh["SH-WEIGHT"]))
            * qty * (dec(100) - qty / dec(4)) / dec(100), rounded=True)
    add(ws["WS-CHARGE"], ws["WS-TOTAL"])
    move(ws["WS-CHARGE"], ws["WS-OUT-CHARGE"])
    out += display_line(sh["SH-ZONE"], sh["SH-CLASS"], " ", sh["SH-QTY"], " x ", sh["SH-WEIGHT"], " = ",
                        ws["WS-OUT-CHARGE"])


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = working_storage()
    sh = Storage("SHIP-REC", SHIP_REC)
    reader = LineSequentialReader(input_files["SHIPS.DAT"], sh.size)
    out = bytearray()
    while reader.read(sh.record()) is not None:
        price_shipment(sh, ws, out)
    move(ws["WS-TOTAL"], ws["WS-OUT-TOTAL"])
    out += display_line("PRICED ", ws["WS-FOUND"], " MISSING ", ws["WS-MISSING"], " TOTAL ",
                        ws["WS-OUT-TOTAL"])
    return bytes(out), {}

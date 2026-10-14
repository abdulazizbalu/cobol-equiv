from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited, Filler,
    move, add, compute, dec, display_line,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    rec = Storage("SHIP-REC", [
        Alnum("SH-ZONE", "X(2)"),
        Alnum("SH-CLASS", "X"),
        Num("SH-WEIGHT", "9(3)V9"),
        Num("SH-QTY", "99"),
    ])
    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
        Group("RATE-DATA", [
            Filler("X(13)", "AAE0450001250"),
            Filler("X(13)", "AAS0300000800"),
            Filler("X(13)", "BKE0600001575"),
            Filler("X(13)", "BKS0420001010"),
            Filler("X(13)", "CNE0725002030"),
            Filler("X(13)", "CNS0510001333"),
            Filler("X(13)", "DEE0999002500"),
            Filler("X(13)", "DES0650001725"),
            Filler("X(13)", "FRE0880002200"),
            Filler("X(13)", "FRS0600001480"),
            Filler("X(13)", "UZE1200003125"),
            Filler("X(13)", "UZS0875002250"),
        ]),
        Group("RATE-TABLE", [
            Group("RT-ENTRY", [
                Alnum("RT-ZONE", "X(2)"),
                Alnum("RT-CLASS", "X"),
                Num("RT-BASE", "9(3)V99"),
                Num("RT-PER-KG", "9(3)V99"),
            ], occurs=12),
        ], redefines="RATE-DATA"),
        Num("WS-CHARGE", "9(7)V99"),
        Num("WS-TOTAL", "9(8)V99", value=0),
        Num("WS-FOUND", "9(3)", value=0),
        Num("WS-MISSING", "9(3)", value=0),
        Edited("WS-OUT-CHARGE", "Z,ZZZ,ZZ9.99"),
        Edited("WS-OUT-TOTAL", "ZZ,ZZZ,ZZ9.99"),
    ])

    out = bytearray()
    reader = LineSequentialReader(input_files.get("SHIPS.DAT", b""), 9)

    def search_all():
        zone = rec["SH-ZONE"].raw
        cls = rec["SH-CLASS"].raw
        key = zone + cls
        lo, hi = 1, 12
        while lo <= hi:
            mid = (lo + hi) // 2
            k = ws.f("RT-ZONE", mid).raw + ws.f("RT-CLASS", mid).raw
            if k == key:
                return mid
            if k < key:
                lo = mid + 1
            else:
                hi = mid - 1
        return None

    def price_shipment():
        rx = search_all()
        if rx is None:
            add(1, ws["WS-MISSING"])
            out.extend(display_line("NO RATE ", rec["SH-ZONE"], "/", rec["SH-CLASS"]))
            return
        add(1, ws["WS-FOUND"])
        qty = dec(rec["SH-QTY"])
        compute(
            ws["WS-CHARGE"],
            (dec(ws.f("RT-BASE", rx)) + dec(ws.f("RT-PER-KG", rx)) * dec(rec["SH-WEIGHT"]))
            * qty * (dec(100) - qty / dec(4)) / dec(100),
            rounded=True,
        )
        add(ws["WS-CHARGE"], ws["WS-TOTAL"])
        move(ws["WS-CHARGE"], ws["WS-OUT-CHARGE"])
        out.extend(display_line(rec["SH-ZONE"], rec["SH-CLASS"], " ", rec["SH-QTY"],
                                " x ", rec["SH-WEIGHT"], " = ", ws["WS-OUT-CHARGE"]))

    while ws["WS-EOF"].raw != b"Y":
        r = reader.read(rec.record())
        if r is None:
            move("Y", ws["WS-EOF"])
        else:
            price_shipment()

    move(ws["WS-TOTAL"], ws["WS-OUT-TOTAL"])
    out.extend(display_line("PRICED ", ws["WS-FOUND"], " MISSING ", ws["WS-MISSING"],
                            " TOTAL ", ws["WS-OUT-TOTAL"]))
    return bytes(out), {}

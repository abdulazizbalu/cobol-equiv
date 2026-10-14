def _num(s):
    v = 0
    for ch in s:
        v = v * 10 + ((ord(ch) & 0x0F) % 10)
    return v


def main(stdin: bytes, input_files: dict) -> tuple:
    out = []

    def disp(*parts):
        out.append("".join(parts) + "\n")

    parts = [
        ("1010", "BOLT   ", 500),
        ("1020", "NUT    ", 300),
        ("1110", "WASHER ", 50),
        ("2005", "GEAR   ", 10),
        ("2500", "SHAFT  ", 0),
        ("3300", "SPRING ", 120),
        ("4001", "PULLEY ", 7),
        ("7777", "BELT   ", 999),
    ]
    pt_part = [p[0] for p in parts]
    pt_name = [p[1] for p in parts]
    pt_onhand = [p[2] for p in parts]

    sm = {"R": 0, "I": 0, "A": 0, "E": 0, "IN": 0, "OUT": 0, "SHORT": 0}
    last = "    "

    data = input_files.get("TRANS.DAT", b"").decode("latin-1")
    lines = data.split("\n")
    if lines and lines[-1] == "":
        lines.pop()

    for line in lines:
        if line.endswith("\r"):
            line = line[:-1]
        rec = (line + " " * 8)[:8]
        tr_part = rec[0:4]
        tr_code = rec[4]
        tr_qty_s = rec[5:8]
        tr_qty = _num(tr_qty_s)
        key = _num(tr_part)

        # SEARCH ALL (binary search)
        lo, hi = 0, 7
        px = None
        while lo <= hi:
            mid = (lo + hi) // 2
            v = _num(pt_part[mid])
            if v == key:
                px = mid
                break
            if v < key:
                lo = mid + 1
            else:
                hi = mid - 1
        if px is None:
            sm["E"] = (sm["E"] + 1) % 1000
            disp("UNKNOWN PART ", tr_part)
            continue
        last = tr_part

        if tr_code == "R":
            sm["R"] = (sm["R"] + 1) % 1000
            pt_onhand[px] = (pt_onhand[px] + tr_qty) % 10000
            sm["IN"] = (sm["IN"] + tr_qty) % 1000000
            if 500 <= tr_qty <= 999:
                disp("BULK RECEIPT ", tr_part, " ", "%03d" % tr_qty)
        elif tr_code == "I":
            sm["I"] = (sm["I"] + 1) % 1000
            if tr_qty > pt_onhand[px]:
                short = (tr_qty - pt_onhand[px]) % 1000
                sm["SHORT"] = (sm["SHORT"] + short) % 1000000
                sm["OUT"] = (sm["OUT"] + pt_onhand[px]) % 1000000
                pt_onhand[px] = 0
                disp("SHORT ", tr_part, " ", "%03d" % short)
            else:
                pt_onhand[px] -= tr_qty
                sm["OUT"] = (sm["OUT"] + tr_qty) % 1000000
        elif tr_code in "+-" and tr_code != "":
            sm["A"] = (sm["A"] + 1) % 1000
            if tr_code == "+":
                pt_onhand[px] = (pt_onhand[px] + tr_qty) % 10000
            else:
                if tr_qty > pt_onhand[px]:
                    pt_onhand[px] = 0
                else:
                    pt_onhand[px] -= tr_qty
        else:
            sm["E"] = (sm["E"] + 1) % 1000
            disp("BAD CODE ", tr_part, " [", tr_code, "]")

    for i in range(8):
        oh = pt_onhand[i]
        if oh == 0:
            st = "E"
        elif oh < 20:
            st = "L"
        else:
            st = "O"
        disp(pt_part[i], " ", pt_name[i], " ", "%04d" % oh, " ", st)
    disp("R ", "%03d" % sm["R"], " I ", "%03d" % sm["I"], " A ", "%03d" % sm["A"],
         " E ", "%03d" % sm["E"])
    disp("IN ", "%06d" % sm["IN"], " OUT ", "%06d" % sm["OUT"], " SHORT ",
         "%06d" % sm["SHORT"], " LAST [", last, "]")

    return "".join(out).encode("latin-1"), {}

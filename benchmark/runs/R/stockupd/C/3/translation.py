def main(stdin: bytes, input_files: dict) -> tuple:
    out = []

    table = [
        ["1010", "BOLT   ", 500],
        ["1020", "NUT    ", 300],
        ["1110", "WASHER ", 50],
        ["2005", "GEAR   ", 10],
        ["2500", "SHAFT  ", 0],
        ["3300", "SPRING ", 120],
        ["4001", "PULLEY ", 7],
        ["7777", "BELT   ", 999],
    ]

    receipts = issues = adjusts = errors = 0
    sm_in = sm_out = sm_short = 0
    last_part = "    "

    data = input_files.get("TRANS.DAT", b"").decode("latin-1")
    lines = data.split("\n")
    if lines and lines[-1] == "":
        lines.pop()

    for line in lines:
        rec = line[:8].ljust(8)
        part = rec[0:4]
        code = rec[4]
        qty_s = rec[5:8]
        try:
            qty = int(qty_s)
        except ValueError:
            qty = 0

        idx = None
        for i, e in enumerate(table):
            if e[0] == part:
                idx = i
                break
        if idx is None:
            errors = (errors + 1) % 1000
            out.append("UNKNOWN PART " + part)
            continue
        last_part = part
        e = table[idx]

        if code == "R":
            receipts = (receipts + 1) % 1000
            e[2] = (e[2] + qty) % 10000
            sm_in = (sm_in + qty) % 1000000
            if 500 <= qty <= 999:
                out.append("BULK RECEIPT " + part + " " + qty_s)
        elif code == "I":
            issues = (issues + 1) % 1000
            if qty > e[2]:
                short = (qty - e[2]) % 1000
                sm_short = (sm_short + short) % 1000000
                sm_out = (sm_out + e[2]) % 1000000
                e[2] = 0
                out.append("SHORT " + part + " " + "%03d" % short)
            else:
                e[2] -= qty
                sm_out = (sm_out + qty) % 1000000
        elif code in ("+", "-"):
            adjusts = (adjusts + 1) % 1000
            if code == "+":
                e[2] = (e[2] + qty) % 10000
            else:
                if qty > e[2]:
                    e[2] = 0
                else:
                    e[2] -= qty
        else:
            errors = (errors + 1) % 1000
            out.append("BAD CODE " + part + " [" + code + "]")

    for e in table:
        if e[2] == 0:
            st = "E"
        elif e[2] < 20:
            st = "L"
        else:
            st = "O"
        out.append("%s %s %04d %s" % (e[0], e[1], e[2], st))
    out.append("R %03d I %03d A %03d E %03d" % (receipts, issues, adjusts, errors))
    out.append("IN %06d OUT %06d SHORT %06d LAST [%s]" % (sm_in, sm_out, sm_short, last_part))

    text = "".join(s + "\n" for s in out)
    return text.encode("latin-1"), {}

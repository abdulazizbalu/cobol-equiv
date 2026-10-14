def _num(b):
    v = 0
    for c in b:
        v = v * 10 + (c & 0x0F if c != 0x20 else 0) % 10
    return v


def main(stdin: bytes, input_files: dict) -> tuple:
    out = []
    parts = [
        [1010, b"BOLT   ", 500],
        [1020, b"NUT    ", 300],
        [1110, b"WASHER ", 50],
        [2005, b"GEAR   ", 10],
        [2500, b"SHAFT  ", 0],
        [3300, b"SPRING ", 120],
        [4001, b"PULLEY ", 7],
        [7777, b"BELT   ", 999],
    ]
    receipts = issues = adjusts = errors = 0
    sm_in = sm_out = sm_short = 0
    last = b"    "

    data = input_files.get("TRANS.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    for line in lines:
        if line.endswith(b"\r"):
            line = line[:-1]
        rec = (line[:8] + b" " * 8)[:8]
        tr_part_raw = rec[0:4]
        tr_code = rec[4:5]
        tr_qty_raw = rec[5:8]
        tr_part = _num(tr_part_raw)
        tr_qty = _num(tr_qty_raw)

        idx = None
        for i, p in enumerate(parts):
            if p[0] == tr_part:
                idx = i
                break
        if idx is None:
            errors = (errors + 1) % 1000
            out.append(b"UNKNOWN PART " + tr_part_raw + b"\n")
            continue
        last = tr_part_raw
        p = parts[idx]
        if tr_code == b"R":
            receipts = (receipts + 1) % 1000
            p[2] = (p[2] + tr_qty) % 10000
            sm_in = (sm_in + tr_qty) % 1000000
            if 500 <= tr_qty <= 999:
                out.append(b"BULK RECEIPT " + tr_part_raw + b" " + tr_qty_raw + b"\n")
        elif tr_code == b"I":
            issues = (issues + 1) % 1000
            if tr_qty > p[2]:
                short = (tr_qty - p[2]) % 1000
                sm_short = (sm_short + short) % 1000000
                sm_out = (sm_out + p[2]) % 1000000
                p[2] = 0
                out.append(b"SHORT " + tr_part_raw + b" " + b"%03d" % short + b"\n")
            else:
                p[2] = p[2] - tr_qty
                sm_out = (sm_out + tr_qty) % 1000000
        elif tr_code in (b"+", b"-"):
            adjusts = (adjusts + 1) % 1000
            if tr_code == b"+":
                p[2] = (p[2] + tr_qty) % 10000
            else:
                if tr_qty > p[2]:
                    p[2] = 0
                else:
                    p[2] = p[2] - tr_qty
        else:
            errors = (errors + 1) % 1000
            out.append(b"BAD CODE " + tr_part_raw + b" [" + tr_code + b"]\n")

    for p in parts:
        if p[2] == 0:
            st = b"E"
        elif p[2] < 20:
            st = b"L"
        else:
            st = b"O"
        out.append(b"%04d " % p[0] + p[1] + b" " + b"%04d" % p[2] + b" " + st + b"\n")
    out.append(b"R %03d I %03d A %03d E %03d\n" % (receipts, issues, adjusts, errors))
    out.append(b"IN %06d OUT %06d SHORT %06d LAST [" % (sm_in, sm_out, sm_short)
               + last + b"]\n")
    return b"".join(out), {}

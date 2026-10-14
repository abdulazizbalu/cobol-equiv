def _digit(c):
    if 48 <= c <= 57:
        return c - 48
    if c == 32:
        return 0
    return c & 0x0F


def _unsigned(b):
    v = 0
    for c in b:
        v = v * 10 + _digit(c)
    return v


def _signed_trailing(b):
    if not b:
        return 0
    neg = False
    last = b[-1]
    if 0x70 <= last <= 0x79:          # 'p'..'y' -> -0..-9
        neg = True
        ld = last - 0x70
    elif last == 0x7D:                # '}' -> -0
        neg = True
        ld = 0
    elif 0x4A <= last <= 0x52:        # 'J'..'R' -> -1..-9
        neg = True
        ld = last - 0x49
    elif last == 0x7B:                # '{' -> +0
        ld = 0
    elif 0x41 <= last <= 0x49:        # 'A'..'I' -> +1..+9
        ld = last - 0x40
    else:
        ld = _digit(last)
    v = 0
    for c in b[:-1]:
        v = v * 10 + _digit(c)
    v = v * 10 + ld
    return -v if neg else v


def _pad(s, n):
    return (s + " " * n)[:n]


def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get("CUST.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    out = []
    cnt_credit = cnt_default = cnt_watch = cnt_normal = 0
    for line in lines:
        if line.endswith(b"\r"):
            line = line[:-1]
        rec = (line + b" " * 20)[:20]
        cu_id = rec[0:4].decode("latin-1")
        cu_type = rec[4:5]
        age = _unsigned(rec[5:8])
        bal = _signed_trailing(rec[8:17])  # in hundredths
        days = _unsigned(rec[17:20])

        if bal < 0:
            cls = "CREDIT"
            cnt_credit = (cnt_credit + 1) % 1000
        elif days > 90:
            cls = "DEFAULT"
            cnt_default = (cnt_default + 1) % 1000
        elif days > 30 and bal > 100000:
            cls = "WATCH"
            cnt_watch = (cnt_watch + 1) % 1000
        else:
            cls = "NORMAL"
            cnt_normal = (cnt_normal + 1) % 1000

        if cu_type == b"P" and age < 25:
            seg = "YOUNG-P"
        elif cu_type == b"P" and age >= 65:
            seg = "SENIOR-P"
        elif cu_type == b"P":
            seg = "PERSONAL"
        elif cu_type == b"B":
            seg = "BUSINESS"
        elif b"G" <= cu_type <= b"J":
            seg = "PUBLIC"
        else:
            seg = "UNKNOWN"

        if cu_type == b"B":
            if bal > 5000000 or days > 60:
                risk = 3
            elif bal > 1000000:
                risk = 2
            else:
                risk = 1
        else:
            if days == 0 and not bal < 0:
                risk = 0
            elif days > 30 or bal < -50000:
                risk = 2
            else:
                risk = 1

        if 0 <= age <= 17:
            band = "MINOR"
        elif 18 <= age <= 64:
            band = "ADULT"
        else:
            band = "SENIOR"

        out.append(cu_id + " " + _pad(cls, 7) + " " + _pad(seg, 10) + " "
                   + str(risk) + " " + _pad(band, 6) + "\n")

    out.append("CREDIT %03d DEFAULT %03d WATCH %03d NORMAL %03d\n"
               % (cnt_credit, cnt_default, cnt_watch, cnt_normal))
    return "".join(out).encode("latin-1"), {}

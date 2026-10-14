def _digit(c):
    if '0' <= c <= '9':
        return ord(c) - 48
    return ord(c) & 0x0F if c else 0


def _signed_zoned(s):
    """Parse a signed zoned decimal with a trailing overpunched sign."""
    body = s[:-1]
    last = s[-1]
    val = 0
    for c in body:
        val = val * 10 + (_digit(c) % 10)
    neg = False
    if '0' <= last <= '9':
        d = ord(last) - 48
    elif 'p' <= last <= 'y':
        d = ord(last) - ord('p')
        neg = True
    elif last == '{':
        d = 0
    elif 'A' <= last <= 'I':
        d = ord(last) - ord('A') + 1
    elif last == '}':
        d = 0
        neg = True
    elif 'J' <= last <= 'R':
        d = ord(last) - ord('J') + 1
        neg = True
    else:
        d = _digit(last) % 10
    val = val * 10 + d
    return -val if neg else val


def _unsigned(s):
    v = 0
    for c in s:
        v = v * 10 + (_digit(c) % 10)
    return v


def main(stdin, input_files):
    data = input_files.get('CUST.DAT', b'')
    text = data.decode('latin-1')
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    out = []
    cnt_credit = cnt_default = cnt_watch = cnt_normal = 0
    for line in lines:
        rec = line[:20].ljust(20)
        cu_id = rec[0:4]
        cu_type = rec[4]
        cu_age = _unsigned(rec[5:8])
        bal = _signed_zoned(rec[8:17])  # in cents
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

        if cu_type == "P" and cu_age < 25:
            seg = "YOUNG-P"
        elif cu_type == "P" and cu_age >= 65:
            seg = "SENIOR-P"
        elif cu_type == "P":
            seg = "PERSONAL"
        elif cu_type == "B":
            seg = "BUSINESS"
        elif "G" <= cu_type <= "J":
            seg = "PUBLIC"
        else:
            seg = "UNKNOWN"

        if cu_type == "B":
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

        if 0 <= cu_age <= 17:
            band = "MINOR"
        elif 18 <= cu_age <= 64:
            band = "ADULT"
        else:
            band = "SENIOR"

        out.append(cu_id + " " + cls.ljust(7) + " " + seg.ljust(10) + " "
                   + str(risk) + " " + band.ljust(6) + "\n")

    out.append("CREDIT %03d DEFAULT %03d WATCH %03d NORMAL %03d\n"
               % (cnt_credit, cnt_default, cnt_watch, cnt_normal))
    return "".join(out).encode('latin-1'), {}

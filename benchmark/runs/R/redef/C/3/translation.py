# Python translation of the COBOL program REDEF (GnuCOBOL 3.1.2 semantics).

REC_LEN = 30
DAYS = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def _unsigned_value(b: bytes) -> int:
    """Numeric value of an unsigned DISPLAY field (digits taken as low nibble)."""
    v = 0
    for c in b:
        v = v * 10 + (c & 0x0F)
    return v


def _decode_trailing_sign(c: int):
    """Decode a trailing overpunch sign byte. Returns (digit_char, sign)."""
    if 0x30 <= c <= 0x39:
        return c, 1
    if c == 0x20:
        return 0x30, 1
    if 0x70 <= c <= 0x79:          # 'p'..'y' : negative 0..9
        return c - 0x40, -1
    if c == 0x7B:                  # '{' : positive 0
        return 0x30, 1
    if 0x41 <= c <= 0x49:          # 'A'..'I' : positive 1..9
        return c - 0x10, 1
    if c == 0x7D:                  # '}' : negative 0
        return 0x30, -1
    if 0x4A <= c <= 0x52:          # 'J'..'R' : negative 1..9
        return c - 0x19, -1
    return c, 1


def _signed_value(b: bytes) -> int:
    """Value of a signed DISPLAY field with a trailing embedded sign."""
    last, sign = _decode_trailing_sign(b[-1])
    v = 0
    for c in b[:-1]:
        v = v * 10 + (c & 0x0F)
    v = v * 10 + (last & 0x0F)
    return sign * v


def _signed_display(b: bytes, scale: int) -> bytes:
    """DISPLAY of a signed numeric DISPLAY field with an implied decimal point."""
    last, sign = _decode_trailing_sign(b[-1])
    digits = bytes(b[:-1]) + bytes([last])
    s = b"-" if sign < 0 else b"+"
    if scale:
        return s + digits[:-scale] + b"." + digits[-scale:]
    return s + digits


def _num_display_signed(value: int, int_digits: int, scale: int) -> bytes:
    s = b"-" if value < 0 else b"+"
    a = abs(value)
    total = int_digits + scale
    d = str(a % (10 ** total)).zfill(total)
    if scale:
        return s + d[:int_digits].encode() + b"." + d[int_digits:].encode()
    return s + d.encode()


def _edit_line(value: int) -> bytes:
    """MOVE S9(9)V99 value to PIC ---,---,--9.99"""
    neg = value < 0
    a = abs(value)
    frac = a % 100
    ip = (a // 100) % (10 ** 8)
    if ip == 0 and frac == 0:
        neg = False
    left = ("-" if neg else "") + f"{ip:,}"
    left = left.rjust(11)
    return (left + "." + f"{frac:02d}").encode()


def main(stdin: bytes, input_files: dict) -> tuple:
    out = []
    data = input_files.get("RECS.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    run_count = 0
    run_total = 0  # in hundredths

    for line in lines:
        rec = line[:REC_LEN]
        if len(rec) < REC_LEN:
            rec = rec + b" " * (REC_LEN - len(rec))
        rtype = rec[0:1]
        body = rec[1:30]

        if rtype == b"H":
            name = body[0:20]
            date = body[20:28]
            yyyy = date[0:4]
            mm = date[4:6]
            dd = date[6:8]
            mmv = _unsigned_value(mm)
            ddv = _unsigned_value(dd)
            ok = b"Y"
            if mmv < 1 or mmv > 12:
                ok = b"N"
            else:
                if ddv < 1 or ddv > DAYS[mmv - 1]:
                    ok = b"N"
            out.append(b"HEADER " + name + b" " + yyyy + b"-" + mm + b"-" + dd
                       + b" " + ok + b" " + date + b"\n")
        elif rtype == b"D":
            item = body[0:5]
            qty = _signed_value(body[5:9])
            price = _unsigned_value(body[9:16])     # hundredths
            disc = _unsigned_value(body[16:18])     # hundredths
            raw = qty * price * (100 - disc)        # 10^-4 units
            neg = raw < 0
            a = abs(raw)
            q, r = divmod(a, 100)
            if r >= 50:
                q += 1
            q %= 10 ** 11
            amt = -q if neg else q
            run_count = (run_count + 1) % 100000
            nt = run_total + amt
            sgn = -1 if nt < 0 else 1
            run_total = sgn * (abs(nt) % (10 ** 11))
            out.append(b"DETAIL " + item + b" " + _edit_line(amt) + b"\n")
        elif rtype == b"T":
            cnt_b = body[0:5]
            tot_b = body[5:16]
            cntv = _unsigned_value(cnt_b)
            totv = _signed_value(tot_b)
            if cntv == run_count and totv == run_total:
                out.append(b"TRAILER OK " + cnt_b + b"\n")
            else:
                out.append(b"TRAILER MISMATCH " + cnt_b + b" "
                           + _signed_display(tot_b, 2) + b" "
                           + str(run_count).zfill(5).encode() + b" "
                           + _num_display_signed(run_total, 9, 2) + b"\n")
            run_count = 0
            run_total = 0
        else:
            out.append(b"UNKNOWN TYPE " + rtype + b"\n")

    out.append(b"OPEN COUNT " + str(run_count).zfill(5).encode() + b" TOTAL "
               + _num_display_signed(run_total, 9, 2) + b"\n")
    return b"".join(out), {}

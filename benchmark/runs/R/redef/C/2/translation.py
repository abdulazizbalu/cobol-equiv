def _digit(b):
    return b & 0x0F


def _unsigned_val(bs):
    v = 0
    for b in bs:
        v = v * 10 + _digit(b)
    return v


def _signed_parse(bs):
    """Return (negative, digit_bytes, value) for trailing overpunched sign DISPLAY field."""
    last = bs[-1]
    neg = False
    if 0x30 <= last <= 0x39:
        d = last - 0x30
    elif 0x70 <= last <= 0x79:
        d = last - 0x70
        neg = True
    else:
        d = last & 0x0F
        if d > 9:
            d = 0
    digits = bytes(bs[:-1]) + bytes([0x30 + d])
    v = 0
    for b in bs[:-1]:
        v = v * 10 + _digit(b)
    v = v * 10 + d
    if neg:
        v = -v
    return neg, digits, v


def _fmt_signed(val, intd, decd):
    s = b"-" if val < 0 else b"+"
    a = abs(val) % (10 ** (intd + decd))
    t = str(a).zfill(intd + decd).encode()
    return s + t[:intd] + b"." + t[intd:]


def _edit(val_cents):
    # PIC ---,---,--9.99
    neg = val_cents < 0
    a = abs(val_cents)
    intpart = (a // 100) % (10 ** 8)
    dec = a % 100
    digs = str(intpart).zfill(8)
    pic = "---,---,--9"
    out = []
    di = 0
    significant = False
    first = True
    for c in pic:
        if c == "-":
            if first:
                first = False
                out.append(" ")
                continue
            d = digs[di]
            di += 1
            if not significant and d == "0":
                out.append(" ")
            else:
                significant = True
                out.append(d)
        elif c == ",":
            out.append("," if significant else " ")
        else:  # '9'
            d = digs[di]
            di += 1
            significant = True
            out.append(d)
    # place floating sign at rightmost space before first digit
    idx = None
    for i in range(len(out)):
        if out[i] != " ":
            break
        idx = i
    if idx is not None:
        out[idx] = "-" if neg else " "
    s = "".join(out) + "." + str(dec).zfill(2)
    return s.encode()


DAYS = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def main(stdin, input_files):
    data = input_files.get("RECS.DAT", b"")
    lines = data.split(b"\n")
    if data.endswith(b"\n"):
        lines = lines[:-1]
    if data == b"":
        lines = []
    out = []
    run_count = 0
    run_total = 0  # cents
    for line in lines:
        rec = line[:30].ljust(30, b" ")
        t = rec[0:1]
        body = rec[1:]
        if t == b"H":
            name = body[0:20]
            date = body[20:28]
            yyyy = date[0:4]
            mm = date[4:6]
            dd = date[6:8]
            mmv = _unsigned_val(mm)
            ddv = _unsigned_val(dd)
            ok = b"Y"
            if mmv < 1 or mmv > 12:
                ok = b"N"
            else:
                if ddv < 1 or ddv > DAYS[mmv - 1]:
                    ok = b"N"
            out.append(b"HEADER " + name + b" " + yyyy + b"-" + mm + b"-" + dd
                       + b" " + ok + b" " + date + b"\n")
        elif t == b"D":
            item = body[0:5]
            _, _, qty = _signed_parse(body[5:9])
            price = _unsigned_val(body[9:16])
            disc = _unsigned_val(body[16:18])
            raw = qty * price * (100 - disc)  # scale 1e-4
            sgn = -1 if raw < 0 else 1
            amt = sgn * ((abs(raw) + 50) // 100)
            amt = sgn * (abs(amt) % (10 ** 11))
            ed = _edit(amt)
            run_count = (run_count + 1) % 100000
            tot = run_total + amt
            ts = -1 if tot < 0 else 1
            run_total = ts * (abs(tot) % (10 ** 11))
            out.append(b"DETAIL " + item + b" " + ed + b"\n")
        elif t == b"T":
            cnt_b = body[0:5]
            cnt = _unsigned_val(cnt_b)
            neg, digits, tv = _signed_parse(body[5:16])
            if cnt == run_count and tv == run_total:
                out.append(b"TRAILER OK " + cnt_b + b"\n")
            else:
                tdisp = (b"-" if neg else b"+") + digits[:9] + b"." + digits[9:11]
                out.append(b"TRAILER MISMATCH " + cnt_b + b" " + tdisp + b" "
                           + str(run_count).zfill(5).encode() + b" "
                           + _fmt_signed(run_total, 9, 2) + b"\n")
            run_count = 0
            run_total = 0
        else:
            out.append(b"UNKNOWN TYPE " + t + b"\n")
    out.append(b"OPEN COUNT " + str(run_count).zfill(5).encode() + b" TOTAL "
               + _fmt_signed(run_total, 9, 2) + b"\n")
    return b"".join(out), {}

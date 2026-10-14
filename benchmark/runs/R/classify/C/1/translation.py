def _d(b):
    if 48 <= b <= 57:
        return b - 48
    return b & 0x0F


def _unsigned(field):
    v = 0
    for b in field:
        v = v * 10 + _d(b)
    return v


def _signed(field):
    # trailing overpunched sign, S9(7)V99 -> value in cents
    neg = False
    last = field[-1]
    if 48 <= last <= 57:
        ld = last - 48
    elif last == 32:
        ld = 0
    elif 0x70 <= last <= 0x79:  # 'p'..'y'
        ld = last - 0x70
        neg = True
    elif last == ord('{'):
        ld = 0
    elif ord('A') <= last <= ord('I'):
        ld = last - ord('A') + 1
    elif last == ord('}'):
        ld = 0
        neg = True
    elif ord('J') <= last <= ord('R'):
        ld = last - ord('J') + 1
        neg = True
    else:
        ld = last & 0x0F
    v = 0
    for b in field[:-1]:
        v = v * 10 + _d(b)
    v = v * 10 + ld
    return -v if neg else v


def main(stdin, input_files):
    data = input_files.get('CUST.DAT', b'')
    lines = data.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
    out = []
    cnt = [0, 0, 0, 0]
    for line in lines:
        if line.endswith(b'\r'):
            line = line[:-1]
        rec = (line + b' ' * 20)[:20]
        cu_id = rec[0:4]
        cu_type = rec[4:5]
        age = _unsigned(rec[5:8])
        bal = _signed(rec[8:17])  # cents
        days = _unsigned(rec[17:20])

        if bal < 0:
            cls = b'CREDIT'
            cnt[0] = (cnt[0] + 1) % 1000
        elif days > 90:
            cls = b'DEFAULT'
            cnt[1] = (cnt[1] + 1) % 1000
        elif days > 30 and bal > 100000:
            cls = b'WATCH'
            cnt[2] = (cnt[2] + 1) % 1000
        else:
            cls = b'NORMAL'
            cnt[3] = (cnt[3] + 1) % 1000

        if cu_type == b'P' and age < 25:
            seg = b'YOUNG-P'
        elif cu_type == b'P' and age >= 65:
            seg = b'SENIOR-P'
        elif cu_type == b'P':
            seg = b'PERSONAL'
        elif cu_type == b'B':
            seg = b'BUSINESS'
        elif b'G' <= cu_type <= b'J':
            seg = b'PUBLIC'
        else:
            seg = b'UNKNOWN'

        if cu_type == b'B':
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
            band = b'MINOR'
        elif 18 <= age <= 64:
            band = b'ADULT'
        else:
            band = b'SENIOR'

        out.append(cu_id + b' ' + cls.ljust(7) + b' ' + seg.ljust(10) + b' '
                   + str(risk).encode() + b' ' + band.ljust(6) + b'\n')

    out.append(b'CREDIT %03d DEFAULT %03d WATCH %03d NORMAL %03d\n' % tuple(cnt))
    return b''.join(out), {}

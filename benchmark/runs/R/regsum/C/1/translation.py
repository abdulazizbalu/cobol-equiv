def _digit(c):
    return c & 0x0F


def _parse_month(b):
    return _digit(b[0]) * 10 + _digit(b[1])


def _parse_amount(b):
    # PIC S9(5)V99, trailing overpunched sign
    val = 0
    for c in b[:-1]:
        val = val * 10 + _digit(c)
    last = b[-1]
    neg = False
    if 0x30 <= last <= 0x39:
        d = last - 0x30
    elif ord('p') <= last <= ord('y'):
        d = last - ord('p')
        neg = True
    elif last == ord('{'):
        d = 0
    elif ord('A') <= last <= ord('I'):
        d = last - ord('A') + 1
    elif last == ord('}'):
        d = 0
        neg = True
    elif ord('J') <= last <= ord('R'):
        d = last - ord('J') + 1
        neg = True
    else:
        d = _digit(last)
    val = val * 10 + d
    return -val if neg else val


def _trunc(v, mod):
    s = -1 if v < 0 else 1
    return s * (abs(v) % mod)


def _edit(v):
    # PIC -(6)9.99 ; v in hundredths
    v = _trunc(v, 10 ** 8)
    neg = v < 0
    a = abs(v)
    ip, fp = divmod(a, 100)
    s = ('-' if neg and a != 0 else '') + str(ip)
    return s.rjust(7) + '.' + '%02d' % fp


def main(stdin, input_files):
    data = input_files.get('SALES.DAT', b'')
    lines = data.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
    out = []

    state = {}

    def init():
        state['region'] = b'  '
        state['name'] = bytearray(b' ' * 10)
        state['amt'] = [0] * 13
        state['cnt'] = [0] * 13
        state['total'] = 0

    def print_region():
        best = 1
        for m in range(1, 13):
            if state['cnt'][m] > 0:
                out.append(state['region'] + b' ' + b'%02d' % m + b' ' +
                           _edit(state['amt'][m]).encode() + b' ' +
                           b'%03d' % state['cnt'][m] + b'\n')
            if state['amt'][m] > state['amt'][best]:
                best = m
        out.append(bytes(state['name']) + b' TOTAL ' +
                   _edit(state['total']).encode() + b' BEST ' +
                   b'%02d' % best + b'\n')

    init()
    first = True
    rejects = 0
    for line in lines:
        rec = line[:11].ljust(11, b' ')
        region = rec[0:2]
        month = _parse_month(rec[2:4])
        amount = _parse_amount(rec[4:11])
        if month < 1 or month > 12:
            rejects = (rejects + 1) % 1000
        else:
            if not first and region != state['region']:
                print_region()
                init()
            first = False
            state['region'] = region
            s = b'REGION ' + region
            state['name'][0:len(s)] = s
            state['amt'][month] = _trunc(state['amt'][month] + amount, 10 ** 8)
            state['total'] = _trunc(state['total'] + amount, 10 ** 9)
            state['cnt'][month] = (state['cnt'][month] + 1) % 1000
    if not first:
        print_region()
    out.append(b'REJECTED ' + b'%03d' % rejects + b'\n')
    return b''.join(out), {}

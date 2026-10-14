def _unpack(b):
    nibbles = []
    for byte in b:
        nibbles.append(byte >> 4)
        nibbles.append(byte & 0x0F)
    digits = nibbles[:-1]
    return ''.join(chr(0x30 + n) for n in digits)


def _edit(b):
    digs = _unpack(b)  # 9 digit characters
    d = digs[:7]
    frac = digs[7:9]
    pattern = list("$$,$$$,$$9.99")
    pos = [1, 3, 4, 5, 7, 8, 9]
    k = 6
    for i in range(6):
        if d[i] != '0':
            k = i
            break
    out = [' '] * 13
    start = pos[k]
    out[start - 1] = '$'
    di = k
    for p in range(start, 13):
        c = pattern[p]
        if c == ',':
            out[p] = ','
        elif c == '.':
            out[p] = '.'
        elif p < 10:
            out[p] = d[di]
            di += 1
        else:
            out[p] = frac[p - 11]
    return ''.join(out).encode('latin-1')


def main(stdin, input_files):
    data = input_files.get('ACCTREC', b'')
    RL = 170
    rec = bytearray(RL)
    out = bytearray()
    i = 0
    while i < len(data):
        chunk = data[i:i + RL]
        i += RL
        rec[:len(chunk)] = chunk
        r = bytes(rec)
        acct_no = r[0:8]
        limit = r[8:13]
        bal = r[13:18]
        last = r[18:38]
        first = r[38:53]
        comments = r[120:170]
        out += acct_no + _edit(limit) + _edit(bal) + last + first + comments
    return b'', {'PRTLINE': bytes(out)}

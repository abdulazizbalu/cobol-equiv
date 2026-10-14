def _digit_val(ch):
    if '0' <= ch <= '9':
        return ord(ch) - 48
    return ord(ch) & 0x0F if ch != ' ' else 0


def _num(s):
    v = 0
    for ch in s:
        v = v * 10 + _digit_val(ch)
    return v


def _edit(value, pic, ndigits):
    digits = str(value).rjust(ndigits, '0')[-ndigits:]
    out = []
    di = 0
    suppress = True
    for p in pic:
        if p == 'Z':
            d = digits[di]
            di += 1
            if suppress and d == '0':
                out.append(' ')
            else:
                suppress = False
                out.append(d)
        elif p == '9':
            d = digits[di]
            di += 1
            suppress = False
            out.append(d)
        elif p == ',':
            out.append(' ' if suppress else ',')
        elif p == '.':
            suppress = False
            out.append('.')
        else:
            out.append(p)
    return ''.join(out)


def main(stdin, input_files):
    data = input_files.get('ITEMS.DAT', b'').decode('latin-1')
    lines = data.split('\n')
    if lines and lines[-1] == '':
        lines.pop()

    out = []
    codes = ['   '] * 8
    qtys = [0] * 8
    amts = [0] * 8  # in cents
    count = 0
    rejected = 0

    for line in lines:
        rec = line[:11].ljust(11)
        code = rec[0:3]
        qty = _num(rec[3:6])
        price = _num(rec[6:11])  # cents
        found = -1
        for t in range(8):
            if codes[t] == code:
                found = t
                break
        if found >= 0:
            qtys[found] = (qtys[found] + qty) % 100000
            amts[found] = (amts[found] + qty * price) % 100000000
        else:
            if count < 8:
                count += 1
                k = count - 1
                codes[k] = code
                qtys[k] = qty % 100000
                amts[k] = (qty * price) % 100000000
            else:
                rejected = (rejected + 1) % 100
                out.append('TABLE FULL ' + code + '\n')

    i = 1
    while not (i >= count):
        j = 1
        while not (j > count - i):
            if amts[j - 1] < amts[j]:
                a, b = j - 1, j
                codes[a], codes[b] = codes[b], codes[a]
                qtys[a], qtys[b] = qtys[b], qtys[a]
                amts[a], amts[b] = amts[b], amts[a]
            j += 1
        i += 1

    for i in range(1, count + 1):
        k = i - 1
        line = (_edit(i, 'Z9', 2) + ' ' + codes[k] + ' ' +
                _edit(qtys[k], 'ZZ,ZZ9', 5) + ' ' +
                _edit(amts[k], 'ZZZ,ZZ9.99', 8))
        out.append(line + '\n')

    out.append('ITEMS %02d REJECTED %02d\n' % (count % 100, rejected % 100))
    return ''.join(out).encode('latin-1'), {}

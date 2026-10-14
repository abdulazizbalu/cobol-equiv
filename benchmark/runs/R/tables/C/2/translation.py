def _edit(value, pic):
    # value: non-negative integer of the digits in pic (decimal point implied by '.')
    ndig = sum(1 for c in pic if c in "Z9")
    digits = str(value).rjust(ndig, "0")[-ndig:]
    out = []
    di = 0
    suppress = True
    for c in pic:
        if c == "Z":
            d = digits[di]
            di += 1
            if suppress and d == "0":
                out.append(" ")
            else:
                suppress = False
                out.append(d)
        elif c == "9":
            d = digits[di]
            di += 1
            suppress = False
            out.append(d)
        elif c == ",":
            out.append(" " if suppress else ",")
        elif c == ".":
            suppress = False
            out.append(".")
        else:
            out.append(c)
    return "".join(out)


def _num(s):
    v = 0
    for ch in s:
        v = v * 10 + (ord(ch) & 0x0F) % 10
    return v


def main(stdin, input_files):
    out = []
    data = input_files.get("ITEMS.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    codes = ["   "] * 8
    qtys = [0] * 8
    amts = [0] * 8  # in hundredths
    count = 0
    rejected = 0

    for raw in lines:
        rec = raw.decode("latin-1")[:11].ljust(11)
        code = rec[0:3]
        qty = _num(rec[3:6])
        price = _num(rec[6:11])  # hundredths
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
                qtys[k] = qty
                amts[k] = (qty * price) % 100000000
            else:
                rejected = (rejected + 1) % 100
                out.append("TABLE FULL " + code + "\n")

    i = 1
    while not (i >= count):
        j = 1
        while not (j > count - i):
            a, b = j - 1, j
            if amts[a] < amts[b]:
                codes[a], codes[b] = codes[b], codes[a]
                qtys[a], qtys[b] = qtys[b], qtys[a]
                amts[a], amts[b] = amts[b], amts[a]
            j += 1
        i += 1

    for i in range(1, count + 1):
        k = i - 1
        line = (_edit(i, "Z9") + " " + codes[k] + " " +
                _edit(qtys[k], "ZZ,ZZ9") + " " +
                _edit(amts[k], "ZZZ,ZZ9.99"))
        out.append(line + "\n")

    out.append("ITEMS %02d REJECTED %02d\n" % (count, rejected))
    return "".join(out).encode("latin-1"), {}

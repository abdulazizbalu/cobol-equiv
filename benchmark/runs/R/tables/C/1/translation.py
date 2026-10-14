def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    data = input_files.get("ITEMS.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    def num(bs):
        v = 0
        for c in bs:
            v = v * 10 + (c & 0x0F) % 10
        return v

    # table: 8 entries, [code(bytes3), qty, amt_cents]
    table = [[b"   ", 0, 0] for _ in range(8)]
    count = 0
    rejected = 0
    out = []

    for line in lines:
        rec = line[:11].ljust(11, b" ")
        code = rec[0:3]
        qty = num(rec[3:6])
        price = num(rec[6:11])  # cents
        found = None
        for t in range(8):
            if table[t][0] == code:
                found = t
                break
        if found is not None:
            e = table[found]
            e[1] = (e[1] + qty) % 100000
            e[2] = (e[2] + qty * price) % 100000000
        else:
            if count < 8:
                count += 1
                e = table[count - 1]
                e[0] = code
                e[1] = qty % 100000
                e[2] = (qty * price) % 100000000
            else:
                rejected = (rejected + 1) % 100
                out.append(b"TABLE FULL " + code + b"\n")

    # bubble sort descending
    i = 1
    while not (i >= count):
        j = 1
        while not (j > count - i):
            if table[j - 1][2] < table[j][2]:
                table[j - 1], table[j] = table[j], table[j - 1]
            j += 1
        i += 1

    for i in range(1, count + 1):
        e = table[i - 1]
        rank = str(i).rjust(2)
        qs = "{:,}".format(e[1]).rjust(6)
        ip, cents = divmod(e[2], 100)
        am = "{:,}".format(ip).rjust(7) + "." + "%02d" % cents
        out.append(rank.encode("latin-1") + b" " + e[0] + b" " +
                   qs.encode("latin-1") + b" " + am.encode("latin-1") + b"\n")

    out.append(("ITEMS %02d REJECTED %02d\n" % (count, rejected)).encode("latin-1"))
    return b"".join(out), {}

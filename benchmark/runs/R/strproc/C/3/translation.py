def _read_lines(data: bytes):
    recs = []
    if not data:
        return recs
    parts = data.split(b"\n")
    if parts and parts[-1] == b"":
        parts = parts[:-1]
    for p in parts:
        s = p.decode("latin-1")
        s = s[:30].ljust(30)
        recs.append(s)
    return recs


def _unstring(src, ptr, fields_sizes):
    # delimiters: "," then ALL " "
    srclen = len(src)
    offset = ptr - 1
    results = []  # list of (value, delim, count)
    overflow = False
    count = 0
    if offset < 0 or offset >= srclen:
        return results, ptr, 0, True
    for size in fields_sizes:
        if offset >= srclen:
            break
        start = offset
        found = False
        dlm = None
        p = start
        match_size = 0
        while p < srclen:
            c = src[p]
            if c == ",":
                match_size = p - start
                offset += match_size + 1
                dlm = ","
                found = True
                break
            if c == " ":
                match_size = p - start
                offset += match_size + 1
                q = p + 1
                while q < srclen and src[q] == " ":
                    offset += 1
                    q += 1
                dlm = " "
                found = True
                break
            p += 1
        if not found:
            match_size = srclen - start
            offset = srclen
            dlm = None
        val = src[start:start + match_size][:size].ljust(size)
        results.append((val, dlm if dlm is not None else " ", match_size))
        count += 1
    if offset < srclen:
        overflow = True
    return results, offset + 1, count, overflow


def _do_line(text):
    commas = text.count(",")
    lead = len(text) - len(text.lstrip(" "))
    idx = text.find(",")
    region = text if idx < 0 else text[:idx]
    a_s = region.count("A")

    f1 = " " * 8
    f2 = " " * 8
    f3 = " " * 6
    d1 = " "
    c1 = 0
    c2 = 0
    res, ptr, nf, uovf = _unstring(text, 1, [8, 8, 6])
    if len(res) >= 1:
        f1, d1, c1 = res[0]
    if len(res) >= 2:
        f2, _, c2 = res[1]
    if len(res) >= 3:
        f3 = res[2][0]
    nf = nf % 100
    c1 %= 100
    c2 %= 100
    ptr %= 100

    # INSPECT F1
    f1 = f1.replace("A", "4")
    lst = list(f1)
    for i in range(len(lst)):
        if lst[i] == "0":
            lst[i] = "*"
        else:
            break
    f1 = "".join(lst)
    # CONVERTING
    f2 = f2.translate(str.maketrans("ABCDE", "abcde"))
    # F3 after initial B
    bi = f3.find("B")
    if bi >= 0:
        f3 = f3[:bi + 1] + "#" * (len(f3) - bi - 1)

    # STRING
    out = []
    size = 16
    sovf = False
    pieces = []
    sp = f2.find(" ")
    pieces.append(f2 if sp < 0 else f2[:sp])
    pieces.append("/")
    sp = f1.find(" ")
    pieces.append(f1 if sp < 0 else f1[:sp])
    pieces.append("/")
    pieces.append(f3)
    for pc in pieces:
        room = size - len(out)
        if len(pc) <= room:
            out.extend(pc)
        else:
            out.extend(pc[:room])
            sovf = True
            break
    optr = len(out) + 1
    wsout = "".join(out).ljust(16)

    line = ("%02d %02d %02d %02d %02d %s [%s][%s]%02d[%s]%02d[%s] [%s] %02d %s" % (
        commas % 100, lead % 100, a_s % 100, nf, ptr, "Y" if uovf else "N",
        f1, d1, c1, f2, c2, f3, wsout, optr % 100, "Y" if sovf else "N"))
    return line


def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get("LINES.DAT", b"")
    out = []
    for rec in _read_lines(data):
        out.append(_do_line(rec) + "\n")
    return "".join(out).encode("latin-1"), {}

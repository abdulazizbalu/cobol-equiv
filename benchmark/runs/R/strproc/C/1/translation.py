def _read_lines(data: bytes, reclen: int):
    recs = []
    if not data:
        return recs
    parts = data.split(b"\n")
    if parts and parts[-1] == b"":
        parts = parts[:-1]
    for p in parts:
        r = p[:reclen]
        r = r + b" " * (reclen - len(r))
        recs.append(r)
    return recs


def _fit(b: bytes, n: int) -> bytes:
    b = b[:n]
    return b + b" " * (n - len(b))


def _num2(v: int) -> bytes:
    return b"%02d" % (v % 100)


def _do_line(text: bytes) -> bytes:
    n = len(text)
    commas = text.count(b",")
    lead = 0
    while lead < n and text[lead:lead + 1] == b" ":
        lead += 1
    ci = text.find(b",")
    pre = text if ci < 0 else text[:ci]
    a_cnt = pre.count(b"A")

    f1 = b" " * 8
    f2 = b" " * 8
    f3 = b" " * 6
    d1 = b" "
    c1 = 0
    c2 = 0
    nf = 0
    uovf = b"N"
    sovf = b"N"
    ptr = 1

    fields = []
    pos = ptr - 1
    for idx in range(3):
        if pos >= n:
            break
        found = -1
        dlen = 0
        dtext = b""
        i = pos
        while i < n:
            ch = text[i:i + 1]
            if ch == b",":
                found = i
                dlen = 1
                dtext = b","
                break
            if ch == b" ":
                j = i
                while j < n and text[j:j + 1] == b" ":
                    j += 1
                found = i
                dlen = j - i
                dtext = b" "
                break
            i += 1
        if found >= 0:
            data = text[pos:found]
            newpos = found + dlen
        else:
            data = text[pos:]
            dtext = b" "
            newpos = n
        nf += 1
        if idx == 0:
            f1 = _fit(data, 8)
            d1 = _fit(dtext, 1)
            c1 = len(data)
        elif idx == 1:
            f2 = _fit(data, 8)
            c2 = len(data)
        else:
            f3 = _fit(data, 6)
        pos = newpos
    ptr = pos + 1
    if pos < n:
        uovf = b"Y"

    # INSPECT WS-F1 REPLACING ALL "A" BY "4" LEADING "0" BY "*"
    f1l = bytearray(f1)
    marked = [False] * len(f1l)
    for i in range(len(f1l)):
        if f1l[i] == ord("A"):
            f1l[i] = ord("4")
            marked[i] = True
    for i in range(len(f1l)):
        if not marked[i] and f1l[i] == ord("0"):
            f1l[i] = ord("*")
        else:
            break
    f1 = bytes(f1l)

    f2 = f2.translate(bytes.maketrans(b"ABCDE", b"abcde"))

    bi = f3.find(b"B")
    if bi >= 0:
        f3 = f3[:bi + 1] + b"#" * (len(f3) - bi - 1)

    out = bytearray(b" " * 16)
    optr = 1

    def delim(b, d):
        k = b.find(d)
        return b if k < 0 else b[:k]

    sources = [delim(f2, b" "), b"/", delim(f1, b" "), b"/", f3]
    stop = False
    for s in sources:
        for ch in s:
            if optr > 16 or optr < 1:
                sovf = b"Y"
                stop = True
                break
            out[optr - 1] = ch
            optr += 1
        if stop:
            break

    return (_num2(commas) + b" " + _num2(lead) + b" " + _num2(a_cnt) + b" "
            + _num2(nf) + b" " + _num2(ptr) + b" " + uovf + b" "
            + b"[" + f1 + b"][" + d1 + b"]" + _num2(c1)
            + b"[" + f2 + b"]" + _num2(c2) + b"[" + f3 + b"] "
            + b"[" + bytes(out) + b"] " + _num2(optr) + b" " + sovf + b"\n")


def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get("LINES.DAT", b"")
    out = []
    for rec in _read_lines(data, 30):
        out.append(_do_line(rec))
    return b"".join(out), {}

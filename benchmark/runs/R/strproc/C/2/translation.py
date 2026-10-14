def _unstring(src, delims, n_fields, ptr):
    """Emulates GnuCOBOL UNSTRING. delims: list of (bytes, is_all).
    Returns (fields, new_ptr, count_fields, overflow)."""
    size = len(src)
    results = []
    offset = ptr - 1
    overflow = False
    if offset < 0 or offset >= size:
        return results, ptr, 0, True
    for _ in range(n_fields):
        if offset >= size:
            break
        start = offset
        found = False
        p = start
        while p < size and not found:
            for d, is_all in delims:
                dl = len(d)
                if p + dl > size:
                    continue
                if src[p:p + dl] == d:
                    data = src[start:p]
                    offset += (p - start) + dl
                    if is_all:
                        q = p + dl
                        while q < size:
                            if q + dl > size:
                                break
                            if src[q:q + dl] != d:
                                break
                            offset += dl
                            q += dl
                    results.append((data, d))
                    found = True
                    break
            p += 1
        if not found:
            data = src[start:]
            offset = size
            results.append((data, None))
    if offset < size:
        overflow = True
    return results, offset + 1, len(results), overflow


def _fit(b, n):
    b = b[:n]
    return b + b" " * (n - len(b))


def _do_line(text):
    commas = text.count(b",")
    lead = len(text) - len(text.lstrip(b" "))
    ci = text.find(b",")
    before = text if ci < 0 else text[:ci]
    a_s = before.count(b"A")

    f1 = b" " * 8
    f2 = b" " * 8
    f3 = b" " * 6
    d1 = b" "
    c1 = 0
    c2 = 0
    res, ptr, nf, uovf = _unstring(text, [(b",", False), (b" ", True)], 3, 1)
    if len(res) >= 1:
        data, d = res[0]
        f1 = _fit(data, 8)
        d1 = _fit(d, 1) if d is not None else b" "
        c1 = len(data)
    if len(res) >= 2:
        data, d = res[1]
        f2 = _fit(data, 8)
        c2 = len(data)
    if len(res) >= 3:
        data, d = res[2]
        f3 = _fit(data, 6)

    # INSPECT WS-F1 REPLACING ALL "A" BY "4" LEADING "0" BY "*"
    f1 = bytearray(f1)
    for i in range(len(f1)):
        if f1[i] == ord("A"):
            f1[i] = ord("4")
    for i in range(len(f1)):
        if f1[i] == ord("0"):
            f1[i] = ord("*")
        else:
            break
    f1 = bytes(f1)
    # CONVERTING
    f2 = f2.translate(bytes.maketrans(b"ABCDE", b"abcde"))
    # REPLACING CHARACTERS BY "#" AFTER INITIAL "B"
    bi = f3.find(b"B")
    if bi >= 0:
        f3 = f3[:bi + 1] + b"#" * (len(f3) - bi - 1)

    # STRING
    out = bytearray(b" " * 16)
    optr = 1
    sovf = False
    segs = []
    sp = f2.find(b" ")
    segs.append(f2 if sp < 0 else f2[:sp])
    segs.append(b"/")
    sp = f1.find(b" ")
    segs.append(f1 if sp < 0 else f1[:sp])
    segs.append(b"/")
    segs.append(f3)
    off = 0
    for s in segs:
        if sovf:
            break
        if len(s) == 0:
            continue
        rem = 16 - off
        if len(s) <= rem:
            out[off:off + len(s)] = s
            off += len(s)
        else:
            out[off:16] = s[:rem]
            off = 16
            sovf = True
    optr = off + 1

    def n2(v):
        return b"%02d" % (v % 100)

    line = (n2(commas) + b" " + n2(lead) + b" " + n2(a_s) + b" " +
            n2(nf) + b" " + n2(ptr) + b" " + (b"Y" if uovf else b"N") + b" " +
            b"[" + f1 + b"][" + d1 + b"]" + n2(c1) +
            b"[" + f2 + b"]" + n2(c2) + b"[" + f3 + b"] " +
            b"[" + bytes(out) + b"] " + n2(optr) + b" " +
            (b"Y" if sovf else b"N") + b"\n")
    return line


def main(stdin, input_files):
    data = input_files.get("LINES.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    out = []
    for ln in lines:
        text = _fit(ln, 30)
        out.append(_do_line(text))
    return b"".join(out), {}

def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    data = input_files.get("NAMES.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    out = bytearray()

    for line in lines:
        rec = line[:30]
        text = rec + b" " * (30 - len(rec))
        # trailing trim (spaces only)
        ln = 30
        while ln > 0 and text[ln - 1:ln] == b" ":
            ln -= 1
        if ln == 0:
            out += b"EMPTY\n"
            continue
        comma = 0
        i = 1
        while not (i > ln or comma > 0):
            if text[i - 1:i] == b",":
                comma = i
            i += 1
        if comma < 2 or comma == ln:
            out += b"NO SPLIT " + text[:ln] + b"\n"
            continue
        s = comma + 1
        while not (s > ln or text[s - 1:s] != b" "):
            s += 1
        if s > ln:
            out += b"NO SPLIT " + text[:ln] + b"\n"
            continue
        # BUILD-OUTPUT
        wsout = bytearray(b" " * 40)
        n = ln - s + 1
        wsout[0:n] = text[s - 1:s - 1 + n]
        c = wsout[0]
        if 97 <= c <= 122:
            wsout[0] = c - 32
        p = n + 2
        n = comma - 1
        wsout[p - 1:p - 1 + n] = text[0:n]
        p += n
        p -= 1
        words = 1
        for i in range(2, p + 1):
            if wsout[i - 1] != 32 and wsout[i - 2] == 32:
                words += 1
        words %= 100
        out += b"[" + bytes(wsout[:p]) + b"] " + b"%02d" % words + b"\n"

    return bytes(out), {}

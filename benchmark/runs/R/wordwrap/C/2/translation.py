def _width_value(raw: bytes) -> int:
    # Approximate GnuCOBOL handling of a PIC 99 DISPLAY field:
    # each byte contributes its low nibble.
    v = 0
    for b in raw:
        if 0x30 <= b <= 0x39:
            d = b - 0x30
        else:
            d = b & 0x0F
            if d > 9:
                d = d % 10
        v = v * 10 + d
    return v


def main(stdin: bytes, input_files: dict) -> tuple:
    out = []
    data = input_files.get("TEXT.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    state = {"lines": 0}

    for raw in lines:
        rec = raw[:62].ljust(62, b" ")
        wraw = rec[0:2]
        text = rec[2:62]
        width = _width_value(wraw)

        if width < 5 or width > 40:
            out.append(b"BAD WIDTH " + wraw + b"\n")
            continue

        out.append(b"WIDTH " + wraw + b"\n")
        line = bytearray(b" " * 40)
        used = 0

        def flush():
            nonlocal line, used
            state["lines"] = (state["lines"] + 1) % 1000
            out.append(b"|" + bytes(line[:width]) + b"|\n")
            line = bytearray(b" " * 40)
            used = 0

        ptr = 1
        while ptr <= 60:
            # UNSTRING ... DELIMITED BY ALL SPACE
            i = ptr - 1
            j = i
            while j < 60 and text[j] != 0x20:
                j += 1
            word = text[i:j]
            wlen = len(word)
            if j < 60:
                k = j
                while k < 60 and text[k] == 0x20:
                    k += 1
                ptr = k + 1
            else:
                ptr = 61

            if wlen > 0:
                start = 1
                while not (wlen - start < width):
                    if used > 0:
                        flush()
                    piece = word[start - 1:start - 1 + width - 1]
                    piece = piece.ljust(width - 1, b" ")
                    line = bytearray((piece + b" " * 40)[:40])
                    line[width - 1] = ord("-")
                    used = width
                    flush()
                    start = (start + width - 1) % 100
                part = (wlen - start + 1) % 100
                if used > 0 and used + 1 + part > width:
                    flush()
                if used == 0:
                    lptr = 1
                else:
                    lptr = (used + 2) % 100
                src = word[start - 1:start - 1 + part]
                if 1 <= lptr <= 40:
                    for c in src:
                        if lptr > 40:
                            break
                        line[lptr - 1] = c
                        lptr += 1
                used = (lptr - 1) % 100

        if used > 0:
            flush()

    out.append(b"LINES " + ("%03d" % state["lines"]).encode() + b"\n")
    return b"".join(out), {}

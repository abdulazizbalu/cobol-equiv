def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get("TEXT.DAT", b"")
    out = []

    # Split the file into records the way LINE SEQUENTIAL reads them.
    records = []
    if data:
        parts = data.split(b"\n")
        if parts and parts[-1] == b"":
            parts.pop()
        records = parts

    lines_count = 0

    def num(bs):
        v = 0
        for c in bs:
            v = v * 10 + (c & 0x0F)
        return v

    for raw in records:
        rec = raw[:62].ljust(62, b" ")
        width_raw = rec[0:2]
        text = rec[2:62]
        width = num(width_raw)

        if width < 5 or width > 40:
            out.append(b"BAD WIDTH " + width_raw + b"\n")
            continue

        out.append(b"WIDTH " + width_raw + b"\n")
        state = {"line": bytearray(b" " * 40), "used": 0}

        def flush():
            nonlocal lines_count
            lines_count = (lines_count + 1) % 1000
            out.append(b"|" + bytes(state["line"][:width]) + b"|\n")
            state["line"] = bytearray(b" " * 40)
            state["used"] = 0

        ptr = 1
        while ptr <= 60:
            # UNSTRING ... DELIMITED BY ALL SPACE INTO WS-WORD COUNT WS-WLEN
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
            word = word.ljust(60, b" ")

            if wlen > 0:
                # PLACE-WORD
                start = 1
                while not (wlen - start < width):
                    if state["used"] > 0:
                        flush()
                    piece = word[start - 1:start - 1 + width - 1]
                    state["line"] = bytearray(piece.ljust(40, b" ")[:40])
                    state["line"][width - 1] = 0x2D  # "-"
                    state["used"] = width
                    flush()
                    start = (start + width - 1) % 100
                part = (wlen - start + 1) % 100
                if state["used"] > 0 and state["used"] + 1 + part > width:
                    flush()
                if state["used"] == 0:
                    lptr = 1
                else:
                    lptr = (state["used"] + 2) % 100
                src = word[start - 1:start - 1 + part]
                line = state["line"]
                for c in src:
                    if lptr < 1 or lptr > 40:
                        break
                    line[lptr - 1] = c
                    lptr += 1
                state["used"] = (lptr - 1) % 100

        if state["used"] > 0:
            flush()

    out.append(b"LINES " + ("%03d" % lines_count).encode() + b"\n")
    return b"".join(out), {}

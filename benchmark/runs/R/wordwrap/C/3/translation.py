def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get("TEXT.DAT", b"").decode("latin-1")
    lines_in = data.split("\n")
    if lines_in and lines_in[-1] == "":
        lines_in.pop()

    out = []
    state = {"lines": 0}

    for raw in lines_in:
        rec = raw[:62].ljust(62)
        wraw = rec[:2]
        text = rec[2:62]
        try:
            width = int(wraw)
        except ValueError:
            width = 0
            for c in wraw:
                width = width * 10 + (ord(c) & 0x0F) % 10

        if width < 5 or width > 40:
            out.append("BAD WIDTH " + wraw + "\n")
            continue

        out.append("WIDTH " + wraw + "\n")
        line = [" "] * 40
        used = 0

        def flush():
            nonlocal line, used
            state["lines"] = (state["lines"] + 1) % 1000
            out.append("|" + "".join(line[:width]) + "|\n")
            line = [" "] * 40
            used = 0

        ptr = 1
        while ptr <= 60:
            # UNSTRING ... DELIMITED BY ALL SPACE
            i = ptr - 1
            j = i
            while j < 60 and text[j] != " ":
                j += 1
            word = text[i:j]
            wlen = len(word)
            if j < 60:
                k = j
                while k < 60 and text[k] == " ":
                    k += 1
                ptr = k + 1
            else:
                ptr = 61
            word60 = word.ljust(60)

            if wlen > 0:
                start = 1
                while not (wlen - start < width):
                    if used > 0:
                        flush()
                    chunk = word60[start - 1:start - 1 + width - 1]
                    line = list(chunk.ljust(40)[:40])
                    line[width - 1] = "-"
                    used = width
                    flush()
                    start = start + width - 1
                part = wlen - start + 1
                if used > 0 and used + 1 + part > width:
                    flush()
                if used == 0:
                    lptr = 1
                else:
                    lptr = used + 2
                piece = word60[start - 1:start - 1 + part]
                for ch in piece:
                    if lptr > 40:
                        break
                    line[lptr - 1] = ch
                    lptr += 1
                used = lptr - 1
        if used > 0:
            flush()

    out.append("LINES %03d\n" % state["lines"])
    return "".join(out).encode("latin-1"), {}

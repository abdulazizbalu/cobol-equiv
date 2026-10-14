def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    data = input_files.get("days-of-week.txt", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    out = []
    line_num = 1
    largest = 0
    curday = b" " * 50
    SP50 = b" " * 50

    for raw in lines:
        rec = raw[:200]
        dow = rec + b" " * (200 - len(rec))
        if dow == b" " * 200:
            out.append(b" \n")
        else:
            endo2 = 0
            charamt = 0
            abbr = [SP50] * 7
            while not endo2 > 0:
                abptr = 1
                daynum = 1
                abrestart = 0
                charamt = (charamt + 1) % 1000
                abbr = [SP50] * 7
                for _ in range(7):
                    # UNSTRING DOW-LINE DELIMITED BY SPACE INTO CURDAY WITH POINTER ABPTR
                    if 1 <= abptr <= 200:
                        start = abptr - 1
                        idx = dow.find(b" ", start)
                        if idx == -1:
                            field = dow[start:]
                            abptr = 201
                        else:
                            field = dow[start:idx]
                            abptr = idx + 2
                        field = field[:50]
                        curday = field + b" " * (50 - len(field))
                    tmp1 = 50 - curday.count(b" ")
                    if tmp1 > largest:
                        largest = tmp1
                    if curday == SP50:
                        endo2 = 3
                    part = curday[:min(charamt, 50)]
                    curabbr = part + b" " * (50 - len(part))
                    for t in range(7):
                        if abbr[t] == curabbr:
                            abrestart = 1
                    if 1 <= daynum <= 7:
                        abbr[daynum - 1] = curabbr
                    daynum += 1
                if abrestart == 0:
                    endo2 = 1
                if charamt > largest:
                    endo2 = 2
            out.append(b"Line " + b"%03d" % line_num + b": ")
            if endo2 == 3:
                out.append(b"Error: not enough days\n")
            elif endo2 == 2:
                out.append(b"Error: identical days\n")
            else:
                out.append(b"%03d" % charamt + b": ")
                for t in range(7):
                    s = abbr[t].rstrip(b" ")
                    out.append(s)
                    out.append(b".")
                    if t + 1 < 7:
                        out.append(b" ")
                    else:
                        out.append(b"\n")
        line_num = (line_num + 1) % 1000

    return b"".join(out), {}

def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    data = input_files.get("days-of-week.txt", b"")
    text = data.decode("latin-1")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()

    out = []
    largest = 0
    line_num = 1

    for raw in lines:
        dow = raw[:200].ljust(200)
        if dow == " " * 200:
            out.append(" \n")
        else:
            endo2 = 0
            charamt = 0
            items = [" " * 50] * 7
            curday = " " * 50  # persists in working storage across iterations
            while not endo2 > 0:
                abptr = 1
                daynum = 1
                abrestart = 0
                charamt = (charamt + 1) % 1000
                items = [" " * 50] * 7
                for _ in range(7):
                    # UNSTRING DOW-LINE DELIMITED BY SPACE INTO CURDAY WITH POINTER ABPTR
                    if 1 <= abptr <= 200:
                        start = abptr - 1
                        pos = dow.find(" ", start)
                        if pos == -1:
                            field = dow[start:]
                            newoff = 200
                        else:
                            field = dow[start:pos]
                            newoff = pos + 1
                        curday = field[:50].ljust(50)
                        abptr = (newoff + 1) % 1000
                    tmp1 = 50 - curday.count(" ")
                    if tmp1 > largest:
                        largest = tmp1
                    if curday == " " * 50:
                        endo2 = 3
                    curabbr = curday[:min(charamt, 50)].ljust(50)
                    for t in range(7):
                        if items[t] == curabbr:
                            abrestart = 1
                    if 1 <= daynum <= 7:
                        items[daynum - 1] = curabbr
                    daynum += 1
                if abrestart == 0:
                    endo2 = 1
                if charamt > largest:
                    endo2 = 2

            out.append("Line %03d: " % line_num)
            if endo2 == 3:
                out.append("Error: not enough days\n")
            elif endo2 == 2:
                out.append("Error: identical days\n")
            else:
                out.append("%03d: " % charamt)
                for t in range(7):
                    cur = items[t]
                    n = len(cur.rstrip(" "))
                    out.append(cur[:n])
                    out.append(".")
                    if t + 1 < 7:
                        out.append(" ")
                    else:
                        out.append("\n")
        line_num = (line_num + 1) % 1000

    return "".join(out).encode("latin-1"), {}

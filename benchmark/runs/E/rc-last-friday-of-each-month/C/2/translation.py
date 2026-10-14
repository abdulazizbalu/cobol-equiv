import datetime


def _accept_numeric(line: bytes, digits: int) -> int:
    s = line.decode("latin-1")
    s = s.rstrip("\r\n").rstrip(" ")
    intpart = []
    for c in s:
        if c.isdigit():
            intpart.append(c)
        elif c == ".":
            break
        elif c in "+-":
            continue
        else:
            intpart.append(str(ord(c) & 0x0F % 10) if (ord(c) & 0x0F) < 10 else "0")
    ds = "".join(intpart)[-digits:] if intpart else ""
    if ds == "":
        return 0
    return int(ds)


def main(stdin: bytes, input_files: dict) -> tuple:
    out = []
    out.append(b"Enter a calendar year (1601 thru 9999): ")
    lines = stdin.split(b"\n")
    if stdin == b"":
        yr = 0
    else:
        yr = _accept_numeric(lines[0], 4)
    if not (1601 <= yr <= 9999):
        out.append(b"Invalid year\n")
        return b"".join(out), {}
    for mo in range(1, 13):
        if mo == 12:
            last = datetime.date(yr, 12, 31)
        else:
            last = datetime.date(yr, mo + 1, 1) - datetime.timedelta(days=1)
        dow = last.weekday() + 1  # Monday=1
        dow = (dow - 5) % 7
        da = last.day - dow
        out.append(("%04d-%02d-%02d\n" % (yr, mo, da)).encode("ascii"))
    return b"".join(out), {}

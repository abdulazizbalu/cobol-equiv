def _decode_display(b: bytes) -> int:
    v = 0
    for c in b:
        v = v * 10 + (c & 0x0F)
    return v


def _edit_total(cents: int) -> bytes:
    int_part = cents // 100
    frac = cents % 100
    d = f"{int_part:05d}"
    f = f"{frac:02d}"
    out = []
    suppress = True
    # pattern: Z , Z Z Z 9 . 9 9
    # d[0]
    if suppress and d[0] == "0":
        out.append(" ")
    else:
        suppress = False
        out.append(d[0])
    # comma
    out.append(" " if suppress else ",")
    for i in range(1, 4):
        if suppress and d[i] == "0":
            out.append(" ")
        else:
            suppress = False
            out.append(d[i])
    out.append(d[4])
    out.append(".")
    out.append(f)
    return "".join(out).encode("latin-1")


def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get("VALUES.DAT", b"")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    count = 0
    total = 0  # in hundredths

    for line in lines:
        rec = line[:6]
        if len(rec) < 6:
            rec = rec + b" " * (6 - len(rec))
        code = rec[0:1]
        amt = _decode_display(rec[1:6])
        if code == b"A":
            count = (count + 1) % 1000
            total = (total + amt) % 10000000

    out = b"COUNT " + f"{count:03d}".encode() + b" TOTAL " + _edit_total(total) + b"\n"
    return out, {}

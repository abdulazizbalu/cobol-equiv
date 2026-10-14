def _accept_num4(line: bytes) -> int:
    # Emulates GnuCOBOL cob_move alphanumeric -> unsigned numeric display PIC 9(4)
    ws = b" \t\n\v\f\r"
    n = len(line)
    i = 0
    while i < n and line[i] in ws:
        i += 1
    if i < n and line[i:i + 1] in (b"+", b"-"):
        i += 1
    count = 0
    p = i
    while p < n and line[p] != ord("."):
        if 48 <= line[p] <= 57:
            count += 1
        p += 1
    size = 4
    out = [ord("0")] * 4
    pos = 0
    if count < size:
        pos = size - count
    else:
        while count > size:
            count -= 1
            while True:
                c = line[i]
                i += 1
                if 48 <= c <= 57:
                    break
    dots = 0
    while i < n and pos < 4:
        c = line[i]
        if 48 <= c <= 57:
            out[pos] = c
            pos += 1
        elif c == ord("."):
            if dots > 0:
                break
            dots += 1
        elif not (c in ws or c == ord(",")):
            break
        i += 1
    return int(bytes(out).decode())


TABLE = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"),
    (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"),
    (5, "V"), (4, "IV"), (1, "I"),
]


def main(stdin: bytes, input_files: dict) -> tuple:
    lines = stdin.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    idx = 0

    def accept():
        nonlocal idx
        if idx < len(lines):
            l = lines[idx]
            idx += 1
            return _accept_num4(l)
        return _accept_num4(b" ")

    out = []
    num = accept()
    while num != 0:
        save = num
        if 0 < num < 4000:
            roman = ""
            rx = 0
            while num != 0:
                d, s = TABLE[rx]
                while not (num < d):
                    roman += s
                    num -= d
                rx += 1
            roman = roman[:16].ljust(16)
            out.append("inp=%04d roman=%s\n" % (save, roman))
        else:
            out.append("inp=%04d invalid\n" % save)
        num = accept()
    return "".join(out).encode("latin-1"), {}

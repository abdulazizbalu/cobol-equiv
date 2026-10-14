def main(stdin: bytes, input_files: dict) -> tuple:
    # ACCEPT reads one line
    if stdin:
        nl = stdin.find(b"\n")
        line = stdin if nl < 0 else stdin[:nl]
    else:
        line = b""
    if line.endswith(b"\r"):
        line = line[:-1]

    data = line
    e1 = len(data)
    dec_pt = ord(".")
    num_sep = ord(",")
    int_size = 5
    total = 8
    out = [ord("0")] * total

    def isdigit(c):
        return 48 <= c <= 57

    def isspace(c):
        return c in (32, 9, 10, 11, 12, 13)

    s1 = 0
    while s1 < e1 and isspace(data[s1]):
        s1 += 1

    if s1 < e1 and data[s1] in (ord("+"), ord("-")):
        s1 += 1

    count = 0
    p = s1
    while p < e1 and data[p] != dec_pt:
        if isdigit(data[p]):
            count += 1
        p += 1

    s2 = 0
    if count < int_size:
        s2 = int_size - count
    else:
        while count > int_size:
            count -= 1
            while s1 < e1:
                c = data[s1]
                s1 += 1
                if isdigit(c):
                    break

    cnt = 0
    while s1 < e1 and s2 < total:
        c = data[s1]
        if isdigit(c):
            out[s2] = c
            s2 += 1
        elif c == dec_pt:
            if cnt > 0:
                break
            cnt += 1
        elif not (isspace(c) or c == num_sep):
            break
        s1 += 1

    digits = bytes(out)
    result = digits[:5] + b"." + digits[5:] + b"\n"
    return result, {}

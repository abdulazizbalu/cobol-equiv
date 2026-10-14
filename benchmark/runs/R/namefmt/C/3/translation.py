def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    data = input_files.get("NAMES.DAT", b"")
    out = []

    # Split the file into line sequential records.
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    upper_tbl = bytes.maketrans(
        b"abcdefghijklmnopqrstuvwxyz", b"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )

    for line in lines:
        # Each record is 30 bytes: longer lines are cut, shorter ones get trailing spaces.
        rec = line[:30]
        text = rec + b" " * (30 - len(rec))

        # Find the length without trailing spaces.
        ln = 30
        while ln > 0 and text[ln - 1:ln] == b" ":
            ln -= 1
        if ln == 0:
            out.append(b"EMPTY\n")
            continue

        # Find the first comma.
        comma = 0
        i = 1
        while not (i > ln or comma > 0):
            if text[i - 1:i] == b",":
                comma = i
            i += 1

        if comma < 2 or comma == ln:
            out.append(b"NO SPLIT " + text[:ln] + b"\n")
            continue

        # Skip spaces after the comma.
        s = comma + 1
        while not (s > ln or text[s - 1:s] != b" "):
            s += 1
        if s > ln:
            out.append(b"NO SPLIT " + text[:ln] + b"\n")
            continue

        # BUILD-OUTPUT: move the part after the comma to the front.
        wo = bytearray(b" " * 40)
        n = ln - s + 1
        wo[0:n] = text[s - 1:s - 1 + n]
        wo[0:1] = bytes(wo[0:1]).translate(upper_tbl)
        p = n + 2
        n = comma - 1
        wo[p - 1:p - 1 + n] = text[0:n]
        p = p + n - 1

        # Count the words.
        words = 1
        for i in range(2, p + 1):
            if wo[i - 1] != 0x20 and wo[i - 2] == 0x20:
                words += 1

        out.append(b"[" + bytes(wo[:p]) + b"] " + b"%02d" % (words % 100) + b"\n")

    return b"".join(out), {}

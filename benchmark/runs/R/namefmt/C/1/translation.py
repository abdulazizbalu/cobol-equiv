def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    data = input_files.get("NAMES.DAT", b"")
    out = bytearray()

    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    for line in lines:
        rec = line[:30]
        text = rec + b" " * (30 - len(rec))
        format_name(text, out)

    return bytes(out), {}


def format_name(text: bytes, out: bytearray) -> None:
    ln = 30
    while ln > 0 and text[ln - 1:ln] == b" ":
        ln -= 1
    if ln == 0:
        out += b"EMPTY\n"
        return

    comma = 0
    for i in range(1, ln + 1):
        if text[i - 1:i] == b",":
            comma = i
            break

    if comma < 2 or comma == ln:
        out += b"NO SPLIT " + text[:ln] + b"\n"
        return

    s = comma + 1
    while s <= ln and text[s - 1:s] == b" ":
        s += 1
    if s > ln:
        out += b"NO SPLIT " + text[:ln] + b"\n"
        return

    # BUILD-OUTPUT
    wsout = bytearray(b" " * 40)
    n = ln - s + 1
    wsout[0:n] = text[s - 1:s - 1 + n]
    c = wsout[0]
    if 97 <= c <= 122:
        wsout[0] = c - 32
    p = n + 2
    n = comma - 1
    wsout[p - 1:p - 1 + n] = text[0:n]
    p = p + n - 1
    words = 1
    for i in range(2, p + 1):
        if wsout[i - 1] != 32 and wsout[i - 2] == 32:
            words += 1
    out += b"[" + bytes(wsout[:p]) + b"] " + ("%02d" % (words % 100)).encode("ascii") + b"\n"

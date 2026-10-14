from cobol_equiv.runtime import Storage, Alnum
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()
    fs = Storage("FS", [Alnum("NAME-REC", "X(30)")])
    reader = LineSequentialReader(input_files.get("NAMES.DAT", b""), 30)

    lower = b"abcdefghijklmnopqrstuvwxyz"
    upper = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    table = bytes.maketrans(lower, upper)

    while True:
        rec = reader.read(fs["NAME-REC"])
        if rec is None:
            break
        text = bytes(fs["NAME-REC"].raw)
        text = (text + b" " * 30)[:30]

        ln = 30
        while ln != 0 and text[ln - 1:ln] == b" ":
            ln -= 1
        if ln == 0:
            out += b"EMPTY\n"
            continue

        comma = 0
        i = 1
        while not (i > ln or comma > 0):
            if text[i - 1:i] == b",":
                comma = i
            i += 1

        if comma < 2 or comma == ln:
            out += b"NO SPLIT " + text[:ln] + b"\n"
            continue

        s = comma + 1
        while not (s > ln or text[s - 1:s] != b" "):
            s += 1
        if s > ln:
            out += b"NO SPLIT " + text[:ln] + b"\n"
            continue

        # BUILD-OUTPUT
        wsout = bytearray(b" " * 40)
        n = ln - s + 1
        wsout[0:n] = text[s - 1:s - 1 + n]
        wsout[0:1] = bytes(wsout[0:1]).translate(table)
        p = n + 2
        n = comma - 1
        wsout[p - 1:p - 1 + n] = text[0:n]
        p = p + n - 1
        words = 1
        for i in range(2, p + 1):
            if wsout[i - 1] != 0x20 and wsout[i - 2] == 0x20:
                words += 1
        out += b"[" + bytes(wsout[:p]) + b"] " + ("%02d" % (words % 100)).encode() + b"\n"

    return bytes(out), {}

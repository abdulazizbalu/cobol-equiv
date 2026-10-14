from cobol_equiv.runtime import Storage, Alnum
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()
    rec = Storage("NAME-FILE", [Alnum("NAME-REC", "X(30)")])
    reader = LineSequentialReader(input_files.get("NAMES.DAT", b""), 30)

    lower = b"abcdefghijklmnopqrstuvwxyz"
    upper = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    conv = bytes.maketrans(lower, upper)

    while True:
        r = reader.read(rec["NAME-REC"])
        if r is None:
            break
        text = bytes(rec["NAME-REC"].raw)
        text = (text + b" " * 30)[:30]

        length = 30
        while length > 0 and text[length - 1:length] == b" ":
            length -= 1
        if length == 0:
            out += b"EMPTY\n"
            continue

        comma = 0
        i = 1
        while not (i > length or comma > 0):
            if text[i - 1:i] == b",":
                comma = i
            i += 1

        if comma < 2 or comma == length:
            out += b"NO SPLIT " + text[:length] + b"\n"
            continue

        s = comma + 1
        while not (s > length or text[s - 1:s] != b" "):
            s += 1
        if s > length:
            out += b"NO SPLIT " + text[:length] + b"\n"
            continue

        # BUILD-OUTPUT
        wsout = bytearray(b" " * 40)
        n = length - s + 1
        wsout[0:n] = text[s - 1:s - 1 + n]
        wsout[0:1] = bytes(wsout[0:1]).translate(conv)
        p = n + 2
        n = comma - 1
        wsout[p - 1:p - 1 + n] = text[0:n]
        p = p + n - 1
        words = 1
        for i in range(2, p + 1):
            if wsout[i - 1] != 0x20 and wsout[i - 2] == 0x20:
                words += 1
        out += b"[" + bytes(wsout[0:p]) + b"] " + b"%02d" % (words % 100) + b"\n"

    return bytes(out), {}

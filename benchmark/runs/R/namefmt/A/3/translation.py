from cobol_equiv.runtime import Storage, Alnum
from cobol_equiv.runtime.files import LineSequentialReader


def _format_name(text: bytes) -> bytes:
    # text is exactly 30 bytes (WS-TEXT)
    length = 30
    while length > 0 and text[length - 1:length] == b" ":
        length -= 1
    if length == 0:
        return b"EMPTY\n"

    comma = 0
    i = 1
    while not (i > length or comma > 0):
        if text[i - 1:i] == b",":
            comma = i
        i += 1

    if comma < 2 or comma == length:
        return b"NO SPLIT " + text[:length] + b"\n"

    s = comma + 1
    while not (s > length or text[s - 1:s] != b" "):
        s += 1
    if s > length:
        return b"NO SPLIT " + text[:length] + b"\n"

    # BUILD-OUTPUT
    out = bytearray(b" " * 40)
    n = length - s + 1
    out[0:n] = text[s - 1:s - 1 + n]
    c = out[0]
    if ord("a") <= c <= ord("z"):
        out[0] = c - 32
    p = n + 2
    n = comma - 1
    out[p - 1:p - 1 + n] = text[0:n]
    p = p + n - 1
    words = 1
    for i in range(2, p + 1):
        if out[i - 1] != 0x20 and out[i - 2] == 0x20:
            words += 1
    words %= 100
    return b"[" + bytes(out[:p]) + b"] " + ("%02d" % words).encode("ascii") + b"\n"


def main(stdin: bytes, input_files: dict) -> tuple:
    rec = Storage("NAME-FILE", [Alnum("NAME-REC", "X(30)")])
    reader = LineSequentialReader(input_files.get("NAMES.DAT", b""), 30)
    out = bytearray()
    while True:
        r = reader.read(rec["NAME-REC"])
        if r is None:
            break
        text = rec["NAME-REC"].raw
        if len(text) < 30:
            text = text + b" " * (30 - len(text))
        text = text[:30]
        out += _format_name(text)
    return bytes(out), {}

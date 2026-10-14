from cobol_equiv.runtime import Storage, Alnum
from cobol_equiv.runtime.files import LineSequentialReader


def _upper(b: bytes) -> bytes:
    return bytes((c - 32) if 97 <= c <= 122 else c for c in b)


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()
    rec = Storage("SEDOL-FILE", [Alnum("SEDOL", "X(6)")])
    sedol = rec["SEDOL"]

    data = input_files.get("sedol.txt")
    if data is None:
        return bytes(out), {}
    reader = LineSequentialReader(data, 6)

    weights = [1, 3, 1, 7, 3, 9]
    parts = [0] * 6

    while True:
        r = reader.read(sedol)
        if r is None:
            break
        s = _upper(sedol.raw)
        sedol.set_raw(s)

        for i in range(6):
            c = s[i]
            w = weights[i]
            if (65 <= c <= 90) or c == 32:
                if c in b"AEIOU":
                    out += b"Invalid SEDOL: " + s + b"\n"
                    continue
                parts[i] = abs((c - 65 + 10) * w) % 1000
            elif 48 <= c <= 57:
                parts[i] = ((c - 48) * w) % 1000
            else:
                out += b"Invalid SEDOL: " + s + b"\n"
                continue

        ws = 0
        for i in range(6):
            ws = (ws + parts[i]) % 1000
        cd = (10 - ws % 10) % 10
        out += s + str(cd).encode() + b"\n"

    return bytes(out), {}

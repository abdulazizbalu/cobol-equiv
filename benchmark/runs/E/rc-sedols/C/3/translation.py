def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files.get("sedol.txt")
    out = bytearray()
    if data is None:
        return bytes(out), {}

    weights = [1, 3, 1, 7, 3, 9, 1]
    parts = [0] * 6  # persists across records

    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    for line in lines:
        rec = line[:6].ljust(6, b" ")
        rec = rec.upper()
        for i in range(6):
            c = rec[i]
            if (65 <= c <= 90) or c == 32:  # ALPHABETIC-UPPER includes space
                if c in b"AEIOU":
                    out += b"Invalid SEDOL: " + rec + b"\n"
                    continue
                v = ((c + 1) - 66 + 10) * weights[i]
                parts[i] = abs(v) % 1000
            elif 48 <= c <= 57:
                parts[i] = ((c - 48) * weights[i]) % 1000
            else:
                out += b"Invalid SEDOL: " + rec + b"\n"
                continue
        ws = 0
        for i in range(6):
            ws = (ws + parts[i]) % 1000
        cd = (10 - ws % 10) % 10
        out += rec + str(cd).encode() + b"\n"

    return bytes(out), {}

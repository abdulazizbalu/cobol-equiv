def main(stdin: bytes, input_files: dict) -> tuple:
    out = bytearray()
    data = input_files.get("sedol.txt")
    if data is None:
        # OPEN fails (status 35); loop does not execute
        return bytes(out), {}

    weights = [1, 3, 1, 7, 3, 9, 1]
    parts = [0] * 6

    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    for line in lines:
        rec = line[:6]
        if len(rec) < 6:
            rec = rec + b" " * (6 - len(rec))
        # UPPER-CASE (ASCII)
        rec = bytes((c - 32) if 97 <= c <= 122 else c for c in rec)

        for i in range(6):
            c = rec[i]
            if (65 <= c <= 90) or c == 32:
                if c in b"AEIOU":
                    out += b"Invalid SEDOL: " + rec + b"\n"
                    continue
                v = (c - 65 + 10) * weights[i]
                parts[i] = abs(v) % 1000
            elif 48 <= c <= 57:
                parts[i] = ((c - 48) * weights[i]) % 1000
            else:
                out += b"Invalid SEDOL: " + rec + b"\n"
                continue

        s = 0
        for i in range(6):
            s = (s + parts[i]) % 1000
        check = (10 - s % 10) % 10
        out += rec + str(check).encode() + b"\n"

    return bytes(out), {}

def main(stdin: bytes, input_files: dict) -> tuple:
    out = bytearray()
    data = input_files.get("sedol.txt")
    if data is None:
        # OPEN fails (status 35); loop never runs, CLOSE fails silently
        return b"", {}

    # Split into line-sequential records
    records = []
    pos = 0
    n = len(data)
    while pos < n:
        nl = data.find(b"\n", pos)
        if nl == -1:
            line = data[pos:]
            pos = n
        else:
            line = data[pos:nl]
            pos = nl + 1
        rec = line[:6]
        rec = rec + b" " * (6 - len(rec))
        records.append(rec)

    weights = [1, 3, 1, 7, 3, 9, 1]
    parts = [0] * 6  # persists across records

    for rec in records:
        # FUNCTION UPPER-CASE (ASCII)
        sedol = bytes(
            (c - 32) if 97 <= c <= 122 else c for c in rec
        )
        for i in range(6):
            ch = sedol[i]
            if (65 <= ch <= 90) or ch == 32:
                if ch in b"AEIOU":
                    out += b"Invalid SEDOL: " + sedol + b"\n"
                    continue
                # ORD(c) - ORD("A") + 10 == c - 65 + 10
                val = (ch - 65 + 10) * weights[i]
                parts[i] = abs(val) % 1000
            elif 48 <= ch <= 57:
                parts[i] = ((ch - 48) * weights[i]) % 1000
            else:
                out += b"Invalid SEDOL: " + sedol + b"\n"
                continue

        ws = 0
        for i in range(6):
            ws = (ws + parts[i]) % 1000
        check = (10 - ws % 10) % 10
        out += sedol + str(check).encode("ascii") + b"\n"

    return bytes(out), {}

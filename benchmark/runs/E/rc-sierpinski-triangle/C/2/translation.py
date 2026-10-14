def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    # ACCEPT n (PIC 99)
    lines = stdin.split(b"\n")
    raw = lines[0] if lines else b""
    s = raw.decode("latin-1").rstrip("\r").strip()
    digits = "".join(ch for ch in s if ch.isdigit())
    n = int(digits) % 100 if digits else 0

    # multiply n by 4 giving i-limit ; subtract 1 from i-limit (unsigned PIC 999)
    i_limit = (n * 4) % 1000
    i_limit = abs(i_limit - 1) % 1000

    MOD18 = 10 ** 18
    out = []
    i = 0
    while not (i > i_limit):
        m = (i_limit - i) % 1000
        m = (m * 2) % 1000
        parts = [" " * m]
        c = 1
        k = 0
        while not (k > i):
            r = c % 2
            if r == 0:
                parts.append("  * ")
            else:
                parts.append("    ")
            c = (c * (i - k) // (k + 1)) % MOD18
            k = (k + 1) % 1000
        parts.append(" \n")
        out.append("".join(parts))
        i += 1
        if i >= 1000:
            break
    return "".join(out).encode("latin-1"), {}

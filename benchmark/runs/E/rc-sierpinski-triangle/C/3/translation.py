def main(stdin: bytes, input_files: dict) -> tuple:
    lines = stdin.split(b"\n")
    line = lines[0] if lines else b""
    line = line.rstrip(b"\r")
    digits = "".join(ch for ch in line.decode("latin-1") if ch.isdigit())
    n = int(digits[-2:]) if digits else 0

    i_limit = (n * 4) % 1000
    i_limit = abs(i_limit - 1) % 1000

    out = []
    MOD = 10 ** 18
    i = 0
    while i <= i_limit:
        m = ((i_limit - i) % 1000) if i_limit >= i else (abs(i_limit - i) % 1000)
        m = (m * 2) % 1000
        parts = [" " * m]
        c = 1
        k = 0
        while k <= i:
            r = c % 2
            if r == 0:
                parts.append("  * ")
            else:
                parts.append("    ")
            c = (c * (i - k) // (k + 1)) % MOD
            k += 1
        parts.append(" \n")
        out.append("".join(parts))
        i += 1
    return "".join(out).encode("latin-1"), {}

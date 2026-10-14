def main(stdin: bytes, input_files: dict) -> tuple:
    # ACCEPT n (PIC 99): read the first line and keep its digits.
    line = stdin.split(b"\n", 1)[0].decode("latin-1").strip()
    digits = "".join(ch for ch in line if ch.isdigit())
    n = int(digits[-2:]) if digits else 0

    # MULTIPLY n BY 4 GIVING i-limit, then SUBTRACT 1.
    # i-limit is PIC 999 (unsigned), so a negative result keeps its
    # absolute value and the field holds only 3 digits.
    i_limit = n * 4
    i_limit = abs(i_limit - 1) % 1000

    MOD = 10 ** 18  # C is PIC 9(18); higher-order digits are truncated
    out = []
    i = 0
    while not (i > i_limit):
        m = abs(i_limit - i) % 1000
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
            c = (c * (i - k) // (k + 1)) % MOD
            k += 1
            if k > 999:
                break
        # DISPLAY '' prints a single space (zero-length literal becomes SPACE).
        parts.append(" \n")
        out.append("".join(parts))
        i += 1
        if i > 999:
            break
    return "".join(out).encode("latin-1"), {}

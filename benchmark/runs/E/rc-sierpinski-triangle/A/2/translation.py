from cobol_equiv.runtime import Storage, Num, Stdin


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [Num("N", "99")])
    inp = Stdin(stdin)
    inp.accept(ws["N"])
    n = int(ws["N"])

    MOD18 = 10 ** 18
    i_limit = (n * 4) % 1000
    i_limit = abs(i_limit - 1) % 1000

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
            c = (c * (i - k) // (k + 1)) % MOD18
            k += 1
        parts.append(" \n")
        out.append("".join(parts))
        i += 1

    return "".join(out).encode("latin-1"), {}

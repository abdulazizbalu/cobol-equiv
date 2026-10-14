from cobol_equiv.runtime import Storage, Num, Group, Stdin


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Group("SIERPINSKI", [
            Num("N", "99"),
            Num("I", "999"),
            Num("K", "999"),
            Num("M", "999"),
            Num("C", "9(18)"),
            Num("I-LIMIT", "999"),
            Num("Q", "9(18)"),
            Num("R", "9"),
        ]),
    ])
    inp = Stdin(stdin)
    inp.accept(ws["N"])
    n = int(ws["N"])

    ilim = (n * 4) % 1000
    ilim = abs(ilim - 1) % 1000

    MOD18 = 10 ** 18
    out = []
    i = 0
    while i <= ilim:
        m = abs(ilim - i) % 1000
        m = (m * 2) % 1000
        parts = [b" " * m]
        c = 1
        k = 0
        while k <= i:
            r = c % 2
            if r == 0:
                parts.append(b"  * ")
            else:
                parts.append(b"    ")
            num = c * (i - k)
            den = k + 1
            val = num // den if num >= 0 else -((-num) // den)
            c = abs(val) % MOD18
            k += 1
        parts.append(b" \n")
        out.append(b"".join(parts))
        i += 1
    return b"".join(out), {}

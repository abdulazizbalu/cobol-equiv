from cobol_equiv.runtime import (
    Storage, Group, Num, move, add, subtract, subtract_giving, multiply,
    multiply_giving, divide_remainder, compute, dec, Stdin,
)


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
    n = ws["N"]
    i = ws["I"]
    k = ws["K"]
    m = ws["M"]
    c = ws["C"]
    ilim = ws["I-LIMIT"]
    q = ws["Q"]
    r = ws["R"]

    out = []
    inp = Stdin(stdin)
    inp.accept(n)
    multiply_giving(n, 4, ilim)
    subtract(1, ilim)

    move(0, i)
    while not (int(i) > int(ilim)):
        # sierpinski-paragraph
        subtract_giving(i, ilim, m)
        multiply(2, m)
        times = int(m)
        if times > 0:
            out.append(b" " * times)
        move(1, c)
        move(0, k)
        while not (int(k) > int(i)):
            divide_remainder(c, 2, q, r)
            if int(r) == 0:
                out.append(b"  * ")
            if int(r) != 0:
                out.append(b"    ")
            compute(c, dec(c) * (dec(i) - dec(k)) / (dec(k) + dec(1)))
            add(1, k)
        out.append(b" \n")
        add(1, i)

    return b"".join(out), {}

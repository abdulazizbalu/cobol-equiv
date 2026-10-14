from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, move, add, subtract_giving, multiply_giving,
    divide_giving, display_bytes, Stdin, SPACES,
)


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Group("WS-COMPLEX-CONSTANT", [
            Num("C-REAL", "S9V999"),
            Num("C-IMAGINARY", "S9V999"),
        ]),
        Group("WS-ARGAND-PLANE", [
            Num("X", "S9(9)V999"),
            Num("Y", "S9(9)V999"),
        ]),
        Group("WS-COMPLEX-VARIABLE", [
            Num("Z-REAL", "S9(9)V999"),
            Num("Z-IMAGINARY", "S9(9)V999"),
        ]),
        Group("WS-TEMPORARY-RESULTS", [
            Num("X-SQUARED", "S9(9)V999"),
            Num("Y-SQUARED", "S9(9)V999"),
            Num("X-TIMES-Y", "S9(9)V999"),
            Num("Z-REAL-SQUARED", "S9(9)V999"),
        ]),
        Group("WS-LOOP-COUNTERS", [
            Num("HORIZONTAL", "999"),
            Num("VERTICAL", "999"),
            Num("ITERATIONS", "99"),
        ]),
        Alnum("WS-PLOT-CHARACTER", "X"),
    ])

    out = bytearray()
    inp = Stdin(stdin)

    c_real = ws["C-REAL"]
    c_imag = ws["C-IMAGINARY"]
    x = ws["X"]
    y = ws["Y"]
    z_real = ws["Z-REAL"]
    z_imag = ws["Z-IMAGINARY"]
    x_sq = ws["X-SQUARED"]
    y_sq = ws["Y-SQUARED"]
    x_t_y = ws["X-TIMES-Y"]
    zr_sq = ws["Z-REAL-SQUARED"]
    horiz = ws["HORIZONTAL"]
    vert = ws["VERTICAL"]
    iters = ws["ITERATIONS"]
    plot = ws["WS-PLOT-CHARACTER"]

    inp.accept(c_real)
    inp.accept(c_imag)

    def complex_mult():
        multiply_giving(x, x, x_sq)
        multiply_giving(y, y, y_sq)
        subtract_giving(y_sq, x_sq, z_real)
        add(c_real, z_real)
        multiply_giving(x, y, x_t_y)
        multiply_giving(x_t_y, 2, z_imag)
        add(c_imag, z_imag)
        multiply_giving(z_real, z_real, zr_sq)
        if zr_sq.value > 10000:
            move(SPACES, plot)
        move(z_real, x)
        move(z_imag, y)

    def computation():
        subtract_giving(280, horiz, x)
        subtract_giving(160, vert, y)
        divide_giving(x, 200, x)
        divide_giving(y, 100, y)
        move("#", plot)
        move(1, iters)
        while not (iters.value > 50 or plot.raw == b" "):
            complex_mult()
            add(1, iters)
        out.extend(display_bytes(plot))

    def outer_loop():
        move(1, horiz)
        while not (horiz.value > 560):
            computation()
            add(10, horiz)
        out.extend(b" \n")

    move(1, vert)
    while not (vert.value > 320):
        outer_loop()
        add(10, vert)

    return bytes(out), {}

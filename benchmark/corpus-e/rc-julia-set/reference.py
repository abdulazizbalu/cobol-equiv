"""Reference translation of the Rosetta Code "Julia set" solution julia-set.cob.

Values are kept as integers in thousandths (PIC S9(9)V999): products and
quotients are truncated toward zero to three decimals, and results keep
their low-order nine integer digits."""

from cobol_equiv.runtime import Num, Stdin, Storage

MOD = 10 ** 12


def _fit(v: int) -> int:
    m = abs(v) % MOD
    return -m if v < 0 else m


def _mul(a: int, b: int) -> int:
    p = a * b
    q = abs(p) // 1000
    return _fit(-q if p < 0 else q)


def _div(a: int, d: int) -> int:  # a in thousandths, d an integer
    q = abs(a) // d
    return _fit(-q if a < 0 else q)


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = Storage("WS", [Num("C-REAL", "S9V999"), Num("C-IMAGINARY", "S9V999")])
    inp = Stdin(stdin)
    inp.accept(ws["C-REAL"])
    inp.accept(ws["C-IMAGINARY"])
    cr = int(ws["C-REAL"].value * 1000)
    ci = int(ws["C-IMAGINARY"].value * 1000)
    out = bytearray()
    for vertical in range(1, 321, 10):
        for horizontal in range(1, 561, 10):
            x = _div((horizontal - 280) * 1000, 200)
            y = _div((vertical - 160) * 1000, 100)
            ch = b"#"
            for _ in range(50):
                x2 = _mul(x, x)
                y2 = _mul(y, y)
                zr = _fit(_fit(x2 - y2) + cr)
                xy = _mul(x, y)
                zi = _fit(_fit(xy * 2) + ci)
                zr2 = _mul(zr, zr)
                if zr2 > 10000 * 1000:
                    ch = b" "
                x, y = zr, zi
                if ch == b" ":
                    break
            out += ch
        out += b" \n"  # DISPLAY '' prints one space
    return bytes(out), {}

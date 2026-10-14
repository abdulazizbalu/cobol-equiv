"""Reference translation of the Rosetta Code "Horizontal sundial calculations"
solution horizontal-sundial-calculations.cob."""

from decimal import Decimal, localcontext

from cobol_equiv.runtime import (COMP, Edited, Num, Stdin, Storage, compute, display_line, move,
                                 subtract_giving)

PI = Decimal("3.1415926535897932384626433832795029")  # FUNCTION PI
PREC = 80


def _sin_cos(x: Decimal):
    with localcontext() as c:
        c.prec = PREC
        two_pi = 2 * Decimal("3.14159265358979323846264338327950288419716939937510582097494459230781640628620899862803482534211706798")
        x = x % two_pi
        eps = Decimal(10) ** -(PREC + 5)
        s, term, n = Decimal(0), x, 1
        while abs(term) > eps:
            s += term
            term = -term * x * x / ((n + 1) * (n + 2))
            n += 2
        co, term, n = Decimal(0), Decimal(1), 0
        while abs(term) > eps:
            co += term
            term = -term * x * x / ((n + 1) * (n + 2))
            n += 2
        return +s, +co


def _atan(x: Decimal) -> Decimal:
    with localcontext() as c:
        c.prec = PREC
        half_pi = Decimal("1.57079632679489661923132169163975144209858469968755291048747229615390820314310449931401741267105853399")
        if x < 0:
            return -_atan(-x)
        if x > 1:
            return half_pi - _atan(1 / x)
        # reduce: atan(x) = 2 atan(x / (1 + sqrt(1 + x^2)))
        k = 0
        while x > Decimal("0.1"):
            x = x / (1 + (1 + x * x).sqrt())
            k += 1
        s, term, n, x2 = Decimal(0), x, 1, x * x
        while term:
            s += term / n
            term = -term * x2
            n += 2
            if abs(term) < Decimal(10) ** -(PREC + 5):
                break
        return s * (2 ** k)


def _dec(f) -> Decimal:
    return Decimal(f.value)


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = Storage("WS", [
        Num("LATITUDE", "S9(3)V9(5)", usage=COMP), Num("LONGITUDE", "S9(3)V9(5)", usage=COMP),
        Num("LEGAL-MERIDIAN", "S9(3)V9(5)", usage=COMP), Num("LAT-SINE", "S9(3)V9(5)", usage=COMP),
        Num("DIFF-LONGITUDE", "S9(3)V9(5)", usage=COMP), Edited("LAT-SINE-DISP", "-(3)9.9(5)"),
        Edited("DIFF-LONGITUDE-DISP", "-(3)9.9(5)"), Num("HOUR", "S9", usage=COMP),
        Num("SUN-HOUR-ANGLE", "S9(3)V9(5)", usage=COMP),
        Num("DIAL-HOUR-LINE-ANGLE", "S9(3)V9(5)", usage=COMP), Num("HOUR-DISP", "99"),
        Edited("SUN-HOUR-ANGLE-DISP", "-(3)9.9(5)"), Edited("DIAL-HOUR-LINE-ANGLE-DISP", "-(3)9.9(5)"),
    ])
    inp = Stdin(stdin)
    out = bytearray(b"Enter latitude: ")
    inp.accept(ws["LATITUDE"])
    out += b"Enter longitude: "
    inp.accept(ws["LONGITUDE"])
    out += b"Enter legal meridian: "
    inp.accept(ws["LEGAL-MERIDIAN"])
    out += b" \n"
    with localcontext() as c:
        c.prec = PREC
        arg = _dec(ws["LATITUDE"]) * 2 * PI / 360
    sine, _ = _sin_cos(arg)
    compute(ws["LAT-SINE"], sine)  # no ROUNDED for the first receiver
    compute(ws["LAT-SINE-DISP"], sine, rounded=True)
    out += b"Sine of latitude: " + ws["LAT-SINE-DISP"].raw.strip(b" ") + b"\n"
    subtract_giving([ws["LEGAL-MERIDIAN"]], ws["LONGITUDE"], [ws["DIFF-LONGITUDE"], ws["DIFF-LONGITUDE-DISP"]])
    out += b"Diff longitude: " + ws["DIFF-LONGITUDE-DISP"].raw.strip(b" ") + b"\n"
    out += b" \n"
    out += b"Time   Sun hour angle  Dial hour line angle\n"
    for hour in range(-6, 7):
        move(hour, ws["HOUR"])
        compute(ws["SUN-HOUR-ANGLE"], Decimal(hour) * 15 - _dec(ws["DIFF-LONGITUDE"]), rounded=True)
        with localcontext() as c:
            c.prec = PREC
            a = _dec(ws["SUN-HOUR-ANGLE"]) * 2 * PI / 360
            s, co = _sin_cos(a)
            t = s / co
            dial = _atan(_dec(ws["LAT-SINE"]) * t) * 360 / (2 * PI)
        compute(ws["DIAL-HOUR-LINE-ANGLE"], dial, rounded=True)
        move(hour + 12, ws["HOUR-DISP"])
        move(ws["SUN-HOUR-ANGLE"], ws["SUN-HOUR-ANGLE-DISP"])
        move(ws["DIAL-HOUR-LINE-ANGLE"], ws["DIAL-HOUR-LINE-ANGLE-DISP"])
        out += display_line(ws["HOUR-DISP"], ":00 ", ws["SUN-HOUR-ANGLE-DISP"], "      ",
                            ws["DIAL-HOUR-LINE-ANGLE-DISP"])
    return bytes(out), {}

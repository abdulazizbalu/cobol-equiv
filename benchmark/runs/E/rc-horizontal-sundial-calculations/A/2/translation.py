from decimal import Decimal, localcontext

from cobol_equiv.runtime import (
    Storage, Num, Edited, COMP, compute, subtract_giving, add_giving,
    move, dec, display_line, display_bytes, Stdin,
)

# GnuCOBOL FUNCTION PI value
COB_PI = Decimal("3.1415926535897932384626433832795029")
# High-precision true pi for internal range reduction
TRUE_PI = Decimal(
    "3.14159265358979323846264338327950288419716939937510"
    "58209749445923078164062862089986280348253421170679"
)
PREC = 100


def _sin(x):
    with localcontext() as ctx:
        ctx.prec = PREC
        two_pi = TRUE_PI * 2
        x = x % two_pi  # Decimal % keeps sign of dividend
        if x > TRUE_PI:
            x -= two_pi
        elif x < -TRUE_PI:
            x += two_pi
        term = x
        s = x
        x2 = x * x
        n = 1
        eps = Decimal(10) ** (-(PREC - 5))
        while True:
            term = -term * x2 / ((2 * n) * (2 * n + 1))
            s += term
            n += 1
            if abs(term) < eps:
                break
        return +s


def _cos(x):
    with localcontext() as ctx:
        ctx.prec = PREC
        return _sin(TRUE_PI / 2 - x)


def _tan(x):
    with localcontext() as ctx:
        ctx.prec = PREC
        return _sin(x) / _cos(x)


def _atan(y):
    with localcontext() as ctx:
        ctx.prec = PREC
        if y == 0:
            return Decimal(0)
        neg = y < 0
        y = abs(y)
        inv = False
        if y > 1:
            y = 1 / y
            inv = True
        k = 0
        while y > Decimal("0.1"):
            y = y / (1 + (1 + y * y).sqrt())
            k += 1
        term = y
        s = y
        y2 = y * y
        n = 1
        eps = Decimal(10) ** (-(PREC - 5))
        while True:
            term = -term * y2
            t = term / (2 * n + 1)
            s += t
            n += 1
            if abs(t) < eps:
                break
        s = s * (2 ** k)
        if inv:
            s = TRUE_PI / 2 - s
        if neg:
            s = -s
        return +s


def main(stdin, input_files):
    ws = Storage("WS", [
        Num("LATITUDE", "S9(3)V9(5)", usage=COMP),
        Num("LONGITUDE", "S9(3)V9(5)", usage=COMP),
        Num("LEGAL-MERIDIAN", "S9(3)V9(5)", usage=COMP),
        Num("LAT-SINE", "S9(3)V9(5)", usage=COMP),
        Num("DIFF-LONGITUDE", "S9(3)V9(5)", usage=COMP),
        Edited("LAT-SINE-DISP", "-(3)9.9(5)"),
        Edited("DIFF-LONGITUDE-DISP", "-(3)9.9(5)"),
        Num("HOUR", "S9", usage=COMP),
        Num("SUN-HOUR-ANGLE", "S9(3)V9(5)", usage=COMP),
        Num("DIAL-HOUR-LINE-ANGLE", "S9(3)V9(5)", usage=COMP),
        Num("HOUR-DISP", "99"),
        Edited("SUN-HOUR-ANGLE-DISP", "-(3)9.9(5)"),
        Edited("DIAL-HOUR-LINE-ANGLE-DISP", "-(3)9.9(5)"),
    ])
    inp = Stdin(stdin)
    out = bytearray()

    out += display_bytes("Enter latitude: ")
    inp.accept(ws["LATITUDE"])
    out += display_bytes("Enter longitude: ")
    inp.accept(ws["LONGITUDE"])
    out += display_bytes("Enter legal meridian: ")
    inp.accept(ws["LEGAL-MERIDIAN"])
    out += display_line(" ")

    with localcontext() as ctx:
        ctx.prec = PREC
        arg = ws["LATITUDE"].value * 2 * COB_PI / 360
        s = _sin(arg)
    compute([ws["LAT-SINE"], (ws["LAT-SINE-DISP"], True)], dec(s))
    out += display_line("Sine of latitude: ",
                        ws["LAT-SINE-DISP"].text.strip(" "))

    subtract_giving(ws["LEGAL-MERIDIAN"], ws["LONGITUDE"],
                    [ws["DIFF-LONGITUDE"], ws["DIFF-LONGITUDE-DISP"]])
    out += display_line("Diff longitude: ",
                        ws["DIFF-LONGITUDE-DISP"].text.strip(" "))
    out += display_line(" ")

    out += display_line("Time   Sun hour angle  Dial hour line angle")
    move(-6, ws["HOUR"])
    while not (ws["HOUR"].value > 6):
        compute(ws["SUN-HOUR-ANGLE"],
                dec(ws["HOUR"]) * dec(15) - dec(ws["DIFF-LONGITUDE"]),
                rounded=True)
        with localcontext() as ctx:
            ctx.prec = PREC
            a = ws["SUN-HOUR-ANGLE"].value * 2 * COB_PI / 360
            t = _tan(a)
            v = _atan(ws["LAT-SINE"].value * t) * 360 / (2 * COB_PI)
        compute(ws["DIAL-HOUR-LINE-ANGLE"], dec(v), rounded=True)

        add_giving([12, ws["HOUR"]], ws["HOUR-DISP"])
        move(ws["SUN-HOUR-ANGLE"], ws["SUN-HOUR-ANGLE-DISP"])
        move(ws["DIAL-HOUR-LINE-ANGLE"], ws["DIAL-HOUR-LINE-ANGLE-DISP"])
        out += display_line(ws["HOUR-DISP"], ":00 ", ws["SUN-HOUR-ANGLE-DISP"],
                            "      ", ws["DIAL-HOUR-LINE-ANGLE-DISP"])
        move(int(ws["HOUR"]) + 1, ws["HOUR"])

    return bytes(out), {}

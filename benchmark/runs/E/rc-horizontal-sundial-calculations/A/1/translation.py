from decimal import Decimal, localcontext

from cobol_equiv.runtime import (
    Storage, Num, Edited, COMP, move, compute, subtract_giving, add_giving,
    dec, display_line, Stdin,
)

_PI_TRUE = Decimal(
    "3.14159265358979323846264338327950288419716939937510582097494459230781"
    "640628620899862803482534211706798214808651328230664709384460955058223"
)
# FUNCTION PI as returned by GnuCOBOL
_COB_PI = Decimal("3.1415926535897932384626433832795029")

_PREC = 120


def _reduce(x):
    two_pi = 2 * _PI_TRUE
    k = (x / two_pi).to_integral_value()
    r = x - k * two_pi
    while r > _PI_TRUE:
        r -= two_pi
    while r < -_PI_TRUE:
        r += two_pi
    return r


def _sin(x):
    with localcontext() as ctx:
        ctx.prec = _PREC
        x = _reduce(x)
        term = x
        s = x
        x2 = x * x
        n = 1
        eps = Decimal(10) ** (-(_PREC - 5))
        while True:
            term = -term * x2 / ((n + 1) * (n + 2))
            n += 2
            s += term
            if abs(term) < eps:
                break
        return s


def _cos(x):
    with localcontext() as ctx:
        ctx.prec = _PREC
        x = _reduce(x)
        term = Decimal(1)
        s = Decimal(1)
        x2 = x * x
        n = 0
        eps = Decimal(10) ** (-(_PREC - 5))
        while True:
            term = -term * x2 / ((n + 1) * (n + 2))
            n += 2
            s += term
            if abs(term) < eps:
                break
        return s


def _tan(x):
    with localcontext() as ctx:
        ctx.prec = _PREC
        return _sin(x) / _cos(x)


def _atan(y):
    with localcontext() as ctx:
        ctx.prec = _PREC
        if y == 0:
            return Decimal(0)
        if y < 0:
            return -_atan(-y)
        if y > 1:
            return _PI_TRUE / 2 - _atan(1 / y)
        # argument halving
        k = 0
        while y > Decimal("0.1"):
            y = y / (1 + (1 + y * y).sqrt())
            k += 1
        term = y
        s = y
        y2 = y * y
        n = 1
        eps = Decimal(10) ** (-(_PREC - 5))
        while True:
            term = -term * y2
            n += 2
            t = term / n
            s += t
            if abs(t) < eps:
                break
        return s * (2 ** k)


def main(stdin: bytes, input_files: dict) -> tuple:
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

    def disp_na(s):
        line = display_line(s)
        out.extend(line[:-1] if line.endswith(b"\n") else line)

    disp_na("Enter latitude: ")
    inp.accept(ws["LATITUDE"])
    disp_na("Enter longitude: ")
    inp.accept(ws["LONGITUDE"])
    disp_na("Enter legal meridian: ")
    inp.accept(ws["LEGAL-MERIDIAN"])
    out.extend(display_line(" "))

    with localcontext() as ctx:
        ctx.prec = _PREC
        lat = ws["LATITUDE"].value
        arg = lat * 2 * _COB_PI / 360
        sv = _sin(arg)
    compute(ws["LAT-SINE"], dec(sv))
    compute(ws["LAT-SINE-DISP"], dec(sv), rounded=True)
    out.extend(display_line("Sine of latitude: ",
                            ws["LAT-SINE-DISP"].text.strip(" ")))

    subtract_giving(ws["LEGAL-MERIDIAN"], ws["LONGITUDE"], ws["DIFF-LONGITUDE"])
    subtract_giving(ws["LEGAL-MERIDIAN"], ws["LONGITUDE"], ws["DIFF-LONGITUDE-DISP"])
    out.extend(display_line("Diff longitude: ",
                            ws["DIFF-LONGITUDE-DISP"].text.strip(" ")))
    out.extend(display_line(" "))

    out.extend(display_line("Time   Sun hour angle  Dial hour line angle"))
    h = -6
    move(h, ws["HOUR"])
    while not (int(ws["HOUR"]) > 6):
        compute(ws["SUN-HOUR-ANGLE"],
                dec(ws["HOUR"]) * dec(15) - dec(ws["DIFF-LONGITUDE"]),
                rounded=True)
        with localcontext() as ctx:
            ctx.prec = _PREC
            sha = ws["SUN-HOUR-ANGLE"].value
            ls = ws["LAT-SINE"].value
            x = sha * 2 * _COB_PI / 360
            t = _tan(x)
            a = _atan(ls * t)
            r = a * 360 / (2 * _COB_PI)
        compute(ws["DIAL-HOUR-LINE-ANGLE"], dec(r), rounded=True)

        add_giving([12, ws["HOUR"]], ws["HOUR-DISP"])
        move(ws["SUN-HOUR-ANGLE"], ws["SUN-HOUR-ANGLE-DISP"])
        move(ws["DIAL-HOUR-LINE-ANGLE"], ws["DIAL-HOUR-LINE-ANGLE-DISP"])
        out.extend(display_line(ws["HOUR-DISP"], ":00 ",
                                ws["SUN-HOUR-ANGLE-DISP"], "      ",
                                ws["DIAL-HOUR-LINE-ANGLE-DISP"]))
        h = int(ws["HOUR"]) + 1
        move(h, ws["HOUR"])

    return bytes(out), {}

from decimal import Decimal, localcontext, Context, ROUND_HALF_EVEN

from cobol_equiv.runtime import (
    Storage, Num, Edited, COMP, move, add_giving, subtract_giving,
    compute, dec, display_line, display_bytes, Stdin,
)

_WORK_PREC = 1000
_FUNC_PREC = 400


def _true_pi(prec):
    with localcontext() as c:
        c.prec = prec + 20

        def arctan_inv(n):
            x = Decimal(1) / n
            n2 = n * n
            total = x
            term = x
            k = 1
            eps = Decimal(10) ** (-(prec + 15))
            while True:
                term = term / n2
                t = term / (2 * k + 1)
                if t < eps:
                    break
                if k % 2:
                    total -= t
                else:
                    total += t
                k += 1
            return total

        p = 16 * arctan_inv(5) - 4 * arctan_inv(239)
    return p


with localcontext() as _c:
    _c.prec = _WORK_PREC
    _TPI = _true_pi(_FUNC_PREC + 50)
    _PI96 = Context(prec=96, rounding=ROUND_HALF_EVEN).plus(_TPI)


def _r96(x):
    return Context(prec=96, rounding=ROUND_HALF_EVEN).plus(x)


def _reduce(x):
    two_pi = 2 * _TPI
    k = (x / two_pi).to_integral_value()
    y = x - k * two_pi
    while y > _TPI:
        y -= two_pi
    while y < -_TPI:
        y += two_pi
    return y


def _sin_cos(x):
    with localcontext() as c:
        c.prec = _FUNC_PREC
        y = _reduce(+x)
        eps = Decimal(10) ** (-(_FUNC_PREC - 10))
        y2 = y * y
        # sin
        term = y
        s = y
        n = 1
        while abs(term) > eps:
            term = -term * y2 / ((n + 1) * (n + 2))
            s += term
            n += 2
        # cos
        term = Decimal(1)
        co = Decimal(1)
        n = 0
        while abs(term) > eps:
            term = -term * y2 / ((n + 1) * (n + 2))
            co += term
            n += 2
        return s, co


def _sin(x):
    return _sin_cos(x)[0]


def _tan(x):
    s, co = _sin_cos(x)
    with localcontext() as c:
        c.prec = _FUNC_PREC
        return s / co


def _atan(x):
    with localcontext() as c:
        c.prec = _FUNC_PREC
        x = +x
        if x == 0:
            return Decimal(0)
        neg = x < 0
        y = abs(x)
        inv = False
        if y > 1:
            y = 1 / y
            inv = True
        mult = 1
        for _ in range(3):
            y = y / (1 + (1 + y * y).sqrt())
            mult *= 2
        eps = Decimal(10) ** (-(_FUNC_PREC - 10))
        y2 = y * y
        term = y
        total = y
        n = 1
        while abs(term) > eps:
            term = -term * y2
            total += term / (2 * n + 1)
            n += 1
        r = total * mult
        if inv:
            r = _TPI / 2 - r
        if neg:
            r = -r
        return r


def _scale(d):
    return -d.as_tuple().exponent


def _cdiv(a, b):
    sa = _scale(a)
    sb = _scale(b)
    if sa >= 0:
        tot = sa + 38
    else:
        tot = 38
    num = int(a.scaleb(tot))
    den = int(b.scaleb(sb))
    q = abs(num) // abs(den)
    if (num < 0) != (den < 0):
        q = -q
    return Decimal(q).scaleb(-(tot - sb))


def _fval(ref, scale):
    return Decimal(ref.value).quantize(Decimal(1).scaleb(-scale))


def main(stdin: bytes, input_files: dict) -> tuple:
    with localcontext() as ctx:
        ctx.prec = _WORK_PREC
        return _run(stdin)


def _run(stdin):
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
    out = bytearray()
    inp = Stdin(stdin)

    out += display_bytes("Enter latitude: ")
    inp.accept(ws["LATITUDE"])
    out += display_bytes("Enter longitude: ")
    inp.accept(ws["LONGITUDE"])
    out += display_bytes("Enter legal meridian: ")
    inp.accept(ws["LEGAL-MERIDIAN"])
    out += display_line(" ")

    lat = _fval(ws["LATITUDE"], 5)
    arg = _cdiv(lat * 2 * _PI96, Decimal(360))
    sval = _r96(_sin(arg))
    compute(ws["LAT-SINE"], dec(sval))
    compute(ws["LAT-SINE-DISP"], dec(sval), rounded=True)
    out += display_line("Sine of latitude: ",
                        ws["LAT-SINE-DISP"].text.strip(" "))

    subtract_giving(ws["LEGAL-MERIDIAN"], ws["LONGITUDE"], ws["DIFF-LONGITUDE"])
    subtract_giving(ws["LEGAL-MERIDIAN"], ws["LONGITUDE"], ws["DIFF-LONGITUDE-DISP"])
    out += display_line("Diff longitude: ",
                        ws["DIFF-LONGITUDE-DISP"].text.strip(" "))
    out += display_line(" ")

    out += display_line("Time   Sun hour angle  Dial hour line angle")
    move(-6, ws["HOUR"])
    while int(ws["HOUR"]) <= 6:
        compute(ws["SUN-HOUR-ANGLE"],
                dec(ws["HOUR"]) * dec(15) - dec(ws["DIFF-LONGITUDE"]),
                rounded=True)
        sha = _fval(ws["SUN-HOUR-ANGLE"], 5)
        ls = _fval(ws["LAT-SINE"], 5)
        targ = _cdiv(sha * 2 * _PI96, Decimal(360))
        t = _r96(_tan(targ))
        p = ls * t
        at = _r96(_atan(p))
        res = _cdiv(at * 360, 2 * _PI96)
        compute(ws["DIAL-HOUR-LINE-ANGLE"], dec(res), rounded=True)

        add_giving([12, ws["HOUR"]], ws["HOUR-DISP"])
        move(ws["SUN-HOUR-ANGLE"], ws["SUN-HOUR-ANGLE-DISP"])
        move(ws["DIAL-HOUR-LINE-ANGLE"], ws["DIAL-HOUR-LINE-ANGLE-DISP"])
        out += display_line(ws["HOUR-DISP"], ":00 ", ws["SUN-HOUR-ANGLE-DISP"],
                            "      ", ws["DIAL-HOUR-LINE-ANGLE-DISP"])
        move(int(ws["HOUR"]) + 1, ws["HOUR"])

    return bytes(out), {}

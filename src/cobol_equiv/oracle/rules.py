"""Oracle rules: each produces cases that are run both in GnuCOBOL and in the
Python runtime, and whose output lines must be byte-identical.

A case declares data items (each emitted as `01 G-<name>. 05 <name> ...` so
its raw bytes can be dumped), COBOL statements, the equivalent runtime calls,
and an output spec. Output values are dumped as hex by a COBOL paragraph, so
binary data never touches stdout directly (except for the display_format
rule, whose subject is the DISPLAY statement itself).

Statements and output specs use {X} placeholders for item names; the runner
replaces them with unique per-case names.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Callable

from ..runtime import arith, encoding as enc
from ..runtime.cobdec import dec, scaled_decimal
from ..runtime.move import move
from ..runtime.pic import NUMERIC, parse_pic
from ..runtime.storage import Alnum, Edited, Item, Num
from .cobolgen import alnum_literal, num_literal

SEED = 20261013


@dataclass
class Case:
    rule: str
    params: str
    items: list[Item]
    cobol: list[str]
    py: Callable[[dict], None]
    out: list[tuple[str, str]]  # ("flag", "") | ("hex", "X") | ("disp", "X") | ("len", "X")
    flag: Callable[[dict], bool] | None = None
    meta: dict = field(default_factory=dict)


# ---- value helpers ---------------------------------------------------------

NUM_PICS = [
    "9", "99", "9(4)", "S9(4)", "9(3)V99", "S9(3)V99", "S9(5)V9(3)", "9V9(6)",
    "S99V9(9)", "S9(9)", "S9(9)V9(4)", "S9(18)", "S9(15)V9(3)", "9(10)",
]
BIG_PICS = ["S9(20)V9(10)", "S9(31)", "9(25)V9(6)"]  # DISPLAY / COMP-3 only
USAGES = [enc.DISPLAY, enc.COMP3, enc.COMP, enc.COMP5]


def usages_for(pic: str) -> list[str]:
    p = parse_pic(pic)
    return USAGES if p.digits <= 18 else [enc.DISPLAY, enc.COMP3]


def fit_values(pic: str, rng: random.Random, n_random: int) -> list[Decimal]:
    """Boundary and random values that fit `pic` exactly."""
    p = parse_pic(pic)
    mx = 10**p.digits - 1
    ulps = {0, 1, mx, mx - 1, mx // 2, mx // 10}
    if p.scale:
        ulps |= {5 * 10 ** (p.scale - 1), 10**p.scale, 10**p.scale + 5}
    for _ in range(n_random):
        k = rng.randint(1, p.digits)
        ulps.add(rng.randint(0, 10**k - 1))
    vals = sorted({scaled_decimal(u, p.scale) for u in ulps if 0 <= u <= mx})
    if p.signed:
        vals += [v.copy_negate() for v in vals if v]
    return vals


def pick(rng: random.Random, seq):
    return seq[rng.randrange(len(seq))]


def fmt_item(it: Item) -> str:
    u = "" if it.usage == enc.DISPLAY or it.pic is None or it.pic.category != NUMERIC else f" {it.usage}"
    return f"{it.pic.text}{u}"


# ---- rules -----------------------------------------------------------------

def rule_storage_length(rng):
    cases = []
    pics = NUM_PICS + BIG_PICS + ["9(2)", "9(3)", "9(5)", "S9(8)", "9(17)"]
    for pic in pics:
        for u in usages_for(pic):
            t = Num("T", pic, usage=u)
            cases.append(Case("storage_length", fmt_item(t), [t], [], lambda f: None, [("len", "T")]))
    for pic in ["X", "X(7)", "A(3)", "ZZ9.99", "$$$,$$9.99CR", "+++9", "***.**"]:
        mk = Edited if parse_pic(pic).category == "numeric-edited" else Alnum
        t = mk("T", pic)
        cases.append(Case("storage_length", pic, [t], [], lambda f: None, [("len", "T")]))
    return cases


def rule_default_init(rng):
    cases = []
    for pic in NUM_PICS[:8]:
        for u in usages_for(pic):
            t = Num("T", pic, usage=u)
            cases.append(Case("default_init", fmt_item(t), [t], [], lambda f: None, [("hex", "T")]))
    for pic in ["X(4)", "ZZ9.99", "$$,$$9.99CR", "***.**", "-9(3)"]:
        mk = Edited if parse_pic(pic).category == "numeric-edited" else Alnum
        t = mk("T", pic)
        cases.append(Case("default_init", pic, [t], [], lambda f: None, [("hex", "T")]))
    return cases


def rule_move_literal(rng):
    cases = []
    for pic in NUM_PICS + BIG_PICS:
        for u in usages_for(pic):
            for v in fit_values(pic, rng, 3):
                t = Num("T", pic, usage=u)
                cases.append(Case(
                    "encode_literal", f"MOVE {num_literal(v)} TO {fmt_item(t)}", [t],
                    [f"MOVE {num_literal(v)} TO {{T}}"],
                    (lambda f, v=v: move(v, f["T"])), [("hex", "T")]))
    return cases


def rule_move_num_num(rng, n=500):
    cases = []
    allpics = NUM_PICS + BIG_PICS
    for _ in range(n):
        sp, tp = pick(rng, allpics), pick(rng, allpics)
        su, tu = pick(rng, usages_for(sp)), pick(rng, usages_for(tp))
        v = pick(rng, fit_values(sp, rng, 4))
        s, t = Num("S", sp, usage=su), Num("T", tp, usage=tu)
        cases.append(Case(
            "move_num_to_num", f"{num_literal(v)} {fmt_item(s)} -> {fmt_item(t)}", [s, t],
            [f"MOVE {num_literal(v)} TO {{S}}", "MOVE {S} TO {T}"],
            (lambda f, v=v: (move(v, f["S"]), move(f["S"], f["T"]))), [("hex", "T")]))
    # sign of a zero produced by truncation, for every usage pair
    for su in USAGES:
        for tu in USAGES:
            for sp, tp, v in (("S9V999", "S9V99", "-0.004"), ("S9(6)", "S9(4)", "-10000"),
                              ("S9(6)V99", "S9(3)V9", "-5000.01")):
                s_, t_ = Num("S", sp, usage=su), Num("T", tp, usage=tu)
                cases.append(Case(
                    "move_num_to_num", f"{v} {fmt_item(s_)} -> {fmt_item(t_)} (zero sign)", [s_, t_],
                    [f"MOVE {v} TO {{S}}", "MOVE {S} TO {T}"],
                    (lambda f, v=v: (move(Decimal(v), f["S"]), move(f["S"], f["T"]))), [("hex", "T")]))
    # negative zero produced by truncation, then propagated by MOVE
    for su in (enc.DISPLAY, enc.COMP3):
        for tu in USAGES:
            s, m, t = Num("S", "S9V999", usage=su), Num("M", "S9V99", usage=su), Num("T", "S9(3)V9", usage=tu)
            cases.append(Case(
                "move_num_to_num", f"-0.004 {fmt_item(s)} -> {fmt_item(m)} -> {fmt_item(t)}",
                [s, m, t],
                ["MOVE -0.004 TO {S}", "MOVE {S} TO {M}", "MOVE {M} TO {T}"],
                lambda f: (move(Decimal("-0.004"), f["S"]), move(f["S"], f["M"]), move(f["M"], f["T"])),
                [("hex", "M"), ("hex", "T")]))
    return cases


EDIT_PICS = [
    "ZZZ9", "ZZZ.ZZ", "ZZZ.99", "ZZ,ZZ9.99", "***.**", "**,**9.99", "$$$,$$9.99",
    "$$$,$$9.99CR", "$ZZ,ZZ9.99DB", "---9", "---,--9.99", "+++9.99", "+ZZZ9", "-ZZZ9",
    "ZZZ9-", "ZZZ9+", "ZZZ9.99CR", "9(4).99-", "99/99/99", "999B999", "ZZ9.9900",
    "$$9", "$$$$", "ZZ", "-$$$9.99", "Z(5)9.99-",
]


def rule_edit(rng):
    cases = []
    src_pic = "S9(7)V9(3)"
    base = [Decimal(x) for x in (
        "0", "0.001", "0.005", "0.05", "0.5", "1", "-1", "5", "12.34", "-12.34", "100",
        "999.99", "-999.99", "1000", "1234.5", "-1234.5", "9999.999", "-9999.999",
        "12345.67", "-12345.67", "1000000", "-0.01", "9999999.999", "-9999999.999",
        "10000", "-10000", "100000", "20000.5",
    )]
    for pic in EDIT_PICS:
        for v in base:
            s, t = Num("S", src_pic), Edited("T", pic)
            cases.append(Case(
                "edit", f"{num_literal(v)} -> {pic}", [s, t],
                [f"MOVE {num_literal(v)} TO {{S}}", "MOVE {S} TO {T}"],
                (lambda f, v=v: (move(v, f["S"]), move(f["S"], f["T"]))), [("hex", "T")]))
    return cases


def rule_move_num_alnum(rng):
    cases = []
    for pic in ["9", "9(4)", "S9(4)", "9(10)", "S9(18)", "9(25)"]:
        for u in usages_for(pic):
            vals = fit_values(pic, rng, 2)
            for xn in (1, 3, 6, 12, 30):
                v = pick(rng, vals)
                s, t = Num("S", pic, usage=u), Alnum("T", f"X({xn})")
                cases.append(Case(
                    "move_num_to_alnum", f"{num_literal(v)} {fmt_item(s)} -> X({xn})", [s, t],
                    [f"MOVE {num_literal(v)} TO {{S}}", "MOVE {S} TO {T}"],
                    (lambda f, v=v: (move(v, f["S"]), move(f["S"], f["T"]))), [("hex", "T")]))
    return cases


def rule_move_alnum_num(rng):
    cases = []
    tpics = ["9(4)", "S9(4)", "9(3)V99", "S9(5)V9(3)", "9", "9(12)"]
    for tp in tpics:
        for tu in usages_for(tp):
            for n in (1, 3, 4, 6, 12):
                digits = "".join(str(rng.randint(0, 9)) for _ in range(n))
                s, t = Alnum("S", f"X({n})"), Num("T", tp, usage=tu)
                lit = alnum_literal(digits.encode())
                cases.append(Case(
                    "move_alnum_to_num", f'"{digits}" X({n}) -> {fmt_item(t)}', [s, t],
                    [f"MOVE {lit} TO {{S}}", "MOVE {S} TO {T}"],
                    (lambda f, d=digits: (move(d, f["S"]), move(f["S"], f["T"]))), [("hex", "T")]))
    return cases


NUMBER_TEXTS = [
    "", " ", "0", "7", "-0", "+0", "-123", "+45", "12.5", "-1.239", "0.005", ".5", "-.25",
    "1,234.56", "1,5", " 42 ", "  -7", "9 9", "123456789", "99999.999", "-99999.999",
    "abc", "1x2", "12-", "1.2.3", "- 5", "+-1", "3.", "00012", "1e5", "\t8", "12 a",
]


def rule_move_alnum_text_num(rng):
    """MOVE of alphanumeric items holding number-like text to numeric and
    numeric-edited items (and the cut to the receiver length that ACCEPT
    applies first is not part of this rule)."""
    cases = []
    texts = NUMBER_TEXTS + ["".join(rng.choice("0123456789 .,+-a") for _ in range(rng.randint(1, 9)))
                            for _ in range(20)]
    tpics = ["9(4)", "S9(4)", "9(3)V99", "S9(3)V99", "S9(5)V9(3)", "S9", "9(12)"]
    for txt in texts:
        lit_text = txt.replace("\t", "\x09")
        n = max(1, len(txt))
        for tp in tpics:
            for tu in usages_for(tp):
                s, t = Alnum("S", f"X({n})"), Num("T", tp, usage=tu)
                if "\t" in txt:
                    continue  # a tab cannot be written as an alphanumeric literal here
                lit = alnum_literal(txt.encode()) if txt else "SPACES"
                cases.append(Case(
                    "move_alnum_text_to_num", f'"{lit_text}" X({n}) -> {fmt_item(t)}', [s, t],
                    [f"MOVE {lit} TO {{S}}", "MOVE {S} TO {T}"],
                    (lambda f, x=txt: (move(x, f["S"]), move(f["S"], f["T"]))), [("hex", "T")]))
        for ep in ("ZZZ9.99-", "-(5)9", "$$,$$9.99", "ZZ9"):
            s, t = Alnum("S", f"X({n})"), Edited("T", ep)
            if "\t" in txt:
                continue
            lit = alnum_literal(txt.encode()) if txt else "SPACES"
            cases.append(Case(
                "move_alnum_text_to_num", f'"{lit_text}" X({n}) -> {ep}', [s, t],
                [f"MOVE {lit} TO {{S}}", "MOVE {S} TO {T}"],
                (lambda f, x=txt: (move(x, f["S"]), move(f["S"], f["T"]))), [("hex", "T")]))
    return cases


def rule_move_alnum_alnum(rng):
    cases = []
    texts = ["A", "ABC", "HELLO WORLD", "  LEAD", "TRAIL  ", "12345678901234567890"]
    for txt in texts:
        for sn in (len(txt), 25):
            for tn in (1, 5, 11, 30):
                s, t = Alnum("S", f"X({sn})"), Alnum("T", f"X({tn})")
                lit = alnum_literal(txt.encode())
                cases.append(Case(
                    "move_alnum_to_alnum", f'"{txt}" X({sn}) -> X({tn})', [s, t],
                    [f"MOVE {lit} TO {{S}}", "MOVE {S} TO {T}"],
                    (lambda f, x=txt: (move(x, f["S"]), move(f["S"], f["T"]))), [("hex", "T")]))
    return cases


# ---- arithmetic --------------------------------------------------------------

ARITH_SRC = ["S9(4)", "S9(3)V99", "9(3)V999", "S9(5)V9(3)", "S99V9(9)", "S9(9)V9(4)", "S9(15)V9(3)"]
ARITH_TGT = ["S9(4)", "S9(3)V99", "9(3)V99", "S9(5)V9(3)", "S9V9(6)", "S9(9)V99", "S9(18)", "S9(6)V9"]

OPS = {
    # name: (cobol template, python fn(f, rounded, se) -> err, operand names)
    "add_to": ("ADD {A} {B} TO {T}{R}", lambda f, r, se: arith.add([f["A"], f["B"]], f["T"], rounded=r, on_size_error=se)),
    "add_giving": ("ADD {A} TO {B} GIVING {T}{R}", lambda f, r, se: arith.add_giving([f["A"], f["B"]], f["T"], rounded=r, on_size_error=se)),
    "subtract_from": ("SUBTRACT {A} {B} FROM {T}{R}", lambda f, r, se: arith.subtract([f["A"], f["B"]], f["T"], rounded=r, on_size_error=se)),
    "subtract_giving": ("SUBTRACT {A} FROM {B} GIVING {T}{R}", lambda f, r, se: arith.subtract_giving([f["A"]], f["B"], f["T"], rounded=r, on_size_error=se)),
    "multiply_by": ("MULTIPLY {A} BY {T}{R}", lambda f, r, se: arith.multiply(f["A"], f["T"], rounded=r, on_size_error=se)),
    "multiply_giving": ("MULTIPLY {A} BY {B} GIVING {T}{R}", lambda f, r, se: arith.multiply_giving(f["A"], f["B"], f["T"], rounded=r, on_size_error=se)),
    "divide_into": ("DIVIDE {A} INTO {T}{R}", lambda f, r, se: arith.divide_into(f["A"], f["T"], rounded=r, on_size_error=se)),
    "divide_by_giving": ("DIVIDE {A} BY {B} GIVING {T}{R}", lambda f, r, se: arith.divide_giving(f["A"], f["B"], f["T"], rounded=r, on_size_error=se)),
    "compute": ("COMPUTE {T}{R} = {A} * {B} - {A}", lambda f, r, se: arith.compute(f["T"], dec(f["A"]) * dec(f["B"]) - dec(f["A"]), rounded=r, on_size_error=se)),
}
END = {"add": "END-ADD", "subtract": "END-SUBTRACT", "multiply": "END-MULTIPLY",
       "divide": "END-DIVIDE", "compute": "END-COMPUTE"}


def _tie_value(pic: str, rng) -> Decimal:
    """A value whose last digit is 5 (a rounding tie when one place is dropped)."""
    p = parse_pic(pic)
    if p.scale == 0:
        return Decimal(rng.randint(0, min(10**p.digits - 1, 999)))
    k = rng.randint(0, min(10 ** (p.digits - 1) - 1, 99999)) * 10 + 5
    v = scaled_decimal(k, p.scale)
    return v.copy_negate() if p.signed and rng.random() < 0.5 else v


def rule_arith(rng, n_per_variant=45):
    cases = []
    for opname, (tmpl, fn) in OPS.items():
        verb = opname.split("_")[0]
        for rounded in (False, True):
            for se in (False, True):
                for i in range(n_per_variant):
                    ap, bp, tp = pick(rng, ARITH_SRC), pick(rng, ARITH_SRC), pick(rng, ARITH_TGT)
                    au, bu = pick(rng, usages_for(ap)), pick(rng, usages_for(bp))
                    tu = pick(rng, usages_for(tp))
                    if i % 3 == 0:
                        av, bv = _tie_value(ap, rng), _tie_value(bp, rng)
                    else:
                        av, bv = pick(rng, fit_values(ap, rng, 4)), pick(rng, fit_values(bp, rng, 4))
                    tv = pick(rng, fit_values(tp, rng, 3))
                    if opname.startswith("divide") and i % 9 == 4:  # division by zero
                        if opname == "divide_into":
                            av = Decimal(0)
                        else:
                            bv = Decimal(0)
                    a, b, t = Num("A", ap, usage=au), Num("B", bp, usage=bu), Num("T", tp, usage=tu)
                    r = " ROUNDED" if rounded else ""
                    st = tmpl.replace("{R}", r)
                    if se:
                        st += f' ON SIZE ERROR MOVE "Y" TO SE-FLAG {END[verb]}'
                    params = (f"{opname}{' ROUNDED' if rounded else ''}{' SIZE-ERROR' if se else ''}: "
                              f"A={num_literal(av)} {fmt_item(a)}, B={num_literal(bv)} {fmt_item(b)}, "
                              f"T={num_literal(tv)} {fmt_item(t)}")

                    def py(f, av=av, bv=bv, tv=tv, fn=fn, rounded=rounded, se=se):
                        move(av, f["A"]); move(bv, f["B"]); move(tv, f["T"])
                        return fn(f, rounded, se) and se

                    cases.append(Case(
                        f"arith_{opname}", params, [a, b, t],
                        [f"MOVE {num_literal(av)} TO {{A}}", f"MOVE {num_literal(bv)} TO {{B}}",
                         f"MOVE {num_literal(tv)} TO {{T}}", st],
                        py, [("flag", ""), ("hex", "T")]))
    return cases


def rule_divide_remainder(rng, n=60):
    cases = []
    qpics = ["S9(4)", "S9(3)V9", "9(3)V99", "S9(2)", "S9(5)V9(3)"]
    rpics = ["S9(4)", "S9(3)V99", "S9V9(4)", "9(3)V9", "S9(6)V9(4)"]
    for rounded in (False, True):
        for se in (False, True):
            for i in range(n):
                ap, bp = pick(rng, ARITH_SRC), pick(rng, ARITH_SRC)
                qp, rp = pick(rng, qpics), pick(rng, rpics)
                au, bu = pick(rng, usages_for(ap)), pick(rng, usages_for(bp))
                qu, ru = pick(rng, usages_for(qp)), pick(rng, usages_for(rp))
                av, bv = pick(rng, fit_values(ap, rng, 4)), pick(rng, fit_values(bp, rng, 4))
                if i % 10 == 3:
                    bv = Decimal(0)
                a, b = Num("A", ap, usage=au), Num("B", bp, usage=bu)
                q, rm = Num("Q", qp, usage=qu), Num("R", rp, usage=ru)
                st = f"DIVIDE {{A}} BY {{B}} GIVING {{Q}}{' ROUNDED' if rounded else ''} REMAINDER {{R}}"
                if se:
                    st += ' ON SIZE ERROR MOVE "Y" TO SE-FLAG END-DIVIDE'
                params = (f"divide_remainder{' ROUNDED' if rounded else ''}{' SIZE-ERROR' if se else ''}: "
                          f"A={num_literal(av)} {fmt_item(a)}, B={num_literal(bv)} {fmt_item(b)}, "
                          f"Q {fmt_item(q)}, R {fmt_item(rm)}")

                def py(f, av=av, bv=bv, rounded=rounded, se=se):
                    move(av, f["A"]); move(bv, f["B"])
                    return arith.divide_remainder(f["A"], f["B"], f["Q"], f["R"],
                                                  rounded=rounded, on_size_error=se) and se

                cases.append(Case(
                    "arith_divide_remainder", params, [a, b, q, rm],
                    [f"MOVE {num_literal(av)} TO {{A}}", f"MOVE {num_literal(bv)} TO {{B}}", st],
                    py, [("flag", ""), ("hex", "Q"), ("hex", "R")]))
    return cases


EXPRS = [
    "{A} / {B} * {C}",
    "{A} * {C} / {B}",
    "{A} / {B} / {C}",
    "({A} + {C}) / {B}",
    "{A} - {B} * {C}",
    "- {A} / {B}",
    "{A} / ({B} + {C})",
    "({A} * {B}) / ({C} * {C} + {B})",
    "{A} * {B} * {C} / 3",
]


def rule_compute_expr(rng, n_per_expr=40):
    cases = []
    tpics = ["S9V99", "S9(5)V9(4)", "S9(3)", "S9(9)V9(8)", "S9(2)V9(30)", "S9(18)"]
    opics = ["S9(3)V99", "S9V9(9)", "S9(9)", "S9(5)V9(3)", "9(2)"]
    for ex in EXPRS:
        for i in range(n_per_expr):
            rounded = i % 2 == 1
            tp = pick(rng, tpics)
            tu = pick(rng, usages_for(tp))
            pics = [pick(rng, opics) for _ in range(3)]
            us = [pick(rng, usages_for(p)) for p in pics]
            vals = [pick(rng, fit_values(p, rng, 5)) for p in pics]
            if i < 4:  # classic thirds
                vals = [Decimal(1), Decimal(3), Decimal(3)]
                pics = ["S9(3)V99", "S9(3)V99", "S9(3)V99"]
                us = [enc.DISPLAY] * 3
            a, b, c = (Num(n, p, usage=u) for n, p, u in zip("ABC", pics, us))
            t = Num("T", tp, usage=tu)
            r = " ROUNDED" if rounded else ""
            pyexpr = ex.replace("{A}", "a").replace("{B}", "b").replace("{C}", "c")
            st = f"COMPUTE {{T}}{r} = {ex} ON SIZE ERROR MOVE \"Y\" TO SE-FLAG END-COMPUTE"
            params = (f"COMPUTE{r} T = {ex.replace('{', '').replace('}', '')}: "
                      + ", ".join(f"{n}={num_literal(v)} {fmt_item(x)}" for n, v, x in zip("ABC", vals, (a, b, c)))
                      + f", T {fmt_item(t)}")

            def py(f, vals=vals, pyexpr=pyexpr, rounded=rounded):
                for n, v in zip("ABC", vals):
                    move(v, f[n])
                env = {"a": dec(f["A"]), "b": dec(f["B"]), "c": dec(f["C"])}
                value = eval(pyexpr, {"__builtins__": {}}, env)  # noqa: S307 (fixed expressions above)
                return arith.compute(f["T"], value, rounded=rounded, on_size_error=True)

            cases.append(Case(
                "compute_intermediate", params, [a, b, c, t],
                [f"MOVE {num_literal(v)} TO {{{n}}}" for n, v in zip("ABC", vals)] + [st],
                py, [("flag", ""), ("hex", "T")]))
    return cases


def rule_binary_store(rng):
    cases = []
    tpics = ["S9(4)", "9(4)", "S99", "S9(9)", "9(9)", "S9(3)V99"]
    vals = [Decimal(x) for x in ("9999", "10000", "12345", "32767", "32768", "65535", "65536",
                                 "-1", "-9999", "-10000", "-32768", "-32769", "99999",
                                 "999999999", "1000000000", "2147483647", "2147483648", "127", "128",
                                 "-128", "-129", "255", "256", "99", "100")]
    for tp in tpics:
        for tu in (enc.COMP, enc.COMP5):
            for v in vals:
                s = Num("S", "S9(12)")
                t = Num("T", tp, usage=tu)
                # MOVE (no size error possible)
                cases.append(Case(
                    "binary_store", f"MOVE {num_literal(v)} -> {fmt_item(t)}", [s, t],
                    [f"MOVE {num_literal(v)} TO {{S}}", "MOVE {S} TO {T}"],
                    (lambda f, v=v: (move(v, f["S"]), move(f["S"], f["T"]))), [("hex", "T")]))
                for se in (False, True):
                    st = "ADD {S} TO {T}"
                    if se:
                        st += ' ON SIZE ERROR MOVE "Y" TO SE-FLAG END-ADD'

                    def py(f, v=v, se=se):
                        move(v, f["S"])
                        return arith.add(f["S"], f["T"], on_size_error=se) and se

                    cases.append(Case(
                        "binary_store", f"ADD {num_literal(v)} TO 0 -> {fmt_item(t)}{' SIZE-ERROR' if se else ''}",
                        [s, t], [f"MOVE {num_literal(v)} TO {{S}}", st], py, [("flag", ""), ("hex", "T")]))
    return cases


def rule_display_format(rng):
    cases = []
    for pic in NUM_PICS + BIG_PICS:
        for u in usages_for(pic):
            for v in fit_values(pic, rng, 1)[:: 3]:
                t = Num("T", pic, usage=u)
                cases.append(Case(
                    "display_format", f"DISPLAY {num_literal(v)} {fmt_item(t)}", [t],
                    [f"MOVE {num_literal(v)} TO {{T}}"],
                    (lambda f, v=v: move(v, f["T"])), [("disp", "T")]))
    # negative zero (DISPLAY / COMP-3) produced by an arithmetic store. The
    # receiver has an odd digit count: single-operand ADD into an even-digit
    # COMP-3 item is refused by the runtime (see rule arith_single_operand).
    for u in (enc.DISPLAY, enc.COMP3):
        s, t = Num("S", "S9(7)"), Num("T", "S9(5)", usage=u)
        cases.append(Case(
            "display_format", f"DISPLAY negative zero {fmt_item(t)}", [s, t],
            ["MOVE -100000 TO {S}", "ADD {S} TO {T}"],
            lambda f: (move(Decimal(-100000), f["S"]), arith.add(f["S"], f["T"])), [("disp", "T"), ("hex", "T")]))
    return cases


RULES = {
    "storage_length": rule_storage_length,
    "default_init": rule_default_init,
    "encode_literal": rule_move_literal,
    "move_num_to_num": rule_move_num_num,
    "move_num_to_alnum": rule_move_num_alnum,
    "move_alnum_to_num": rule_move_alnum_num,
    "move_alnum_text_to_num": rule_move_alnum_text_num,
    "move_alnum_to_alnum": rule_move_alnum_alnum,
    "edit": rule_edit,
    "arith": rule_arith,
    "arith_divide_remainder": rule_divide_remainder,
    "compute_intermediate": rule_compute_expr,
    "binary_store": rule_binary_store,
    "display_format": rule_display_format,
}


def all_cases(seed: int = SEED) -> list[Case]:
    out = []
    for name, gen in RULES.items():
        out += gen(random.Random(f"{seed}-{name}"))
    return out


# ---- STRING / UNSTRING / INSPECT -------------------------------------------

def _rtext(rng, alphabet: str, n: int) -> str:
    return "".join(pick(rng, alphabet) for _ in range(n))


def _lit(s: str) -> str:
    return alnum_literal(s.encode("latin-1"))


def rule_string(rng, n=120):
    from ..runtime import text

    cases = []
    for i in range(n):
        a = _rtext(rng, "AB ,-", rng.randint(1, 8))
        b = _rtext(rng, "CD ,", rng.randint(1, 8))
        k = rng.randint(1, 12)
        p0 = pick(rng, [1, 1, 1, 2, k, k + 1, 0, rng.randint(1, k)])
        d1 = pick(rng, [None, " ", ",", "B-"])
        d2 = pick(rng, [None, " ", ","])
        s1, s2 = Alnum("S", f"X({len(a)})"), Alnum("U", f"X({len(b)})")
        t, p = Alnum("T", f"X({k})"), Num("P", "9(3)")
        dtxt = lambda d: "SIZE" if d is None else _lit(d)  # noqa: E731
        st = (f"STRING {{S}} DELIMITED BY {dtxt(d1)} {{U}} DELIMITED BY {dtxt(d2)} "
              f'"*" DELIMITED BY SIZE INTO {{T}} WITH POINTER {{P}} '
              f'ON OVERFLOW MOVE "Y" TO SE-FLAG END-STRING')

        def py(f, a=a, b=b, d1=d1, d2=d2, p0=p0):
            move(a, f["S"]); move(b, f["U"]); move("." * f["T"].size, f["T"]); move(p0, f["P"])
            return text.string([(f["S"], d1), (f["U"], d2), ("*", None)], f["T"], pointer=f["P"])

        cases.append(Case(
            "string_stmt", f'"{a}" BY {d1!r}, "{b}" BY {d2!r}, "*" INTO X({k}) POINTER {p0}',
            [s1, s2, t, p],
            [f"MOVE {_lit(a)} TO {{S}}", f"MOVE {_lit(b)} TO {{U}}", 'MOVE ALL "." TO {T}',
             f"MOVE {p0} TO {{P}}", st],
            py, [("flag", ""), ("hex", "T"), ("hex", "P")]))
    return cases


UNSTRING_DELIMS = [
    [","], [(",", True)], [",", ";"], [(" ", True), ","], [";", (",", True)], [],
]


def rule_unstring(rng, n=150):
    from ..runtime import text

    cases = []
    for i in range(n):
        src = _rtext(rng, "AB,; ", rng.randint(1, 14))
        dl = UNSTRING_DELIMS[i % len(UNSTRING_DELIMS)]
        p0 = pick(rng, [1, 1, 1, 2, len(src), len(src) + 1, 0])
        rw = rng.randint(1, 5)
        items = [Alnum("S", f"X({len(src)})"), Alnum("R1", f"X({rw})"), Alnum("R2", "X(4)"),
                 Alnum("R3", "X(3)"), Alnum("D1", "X(2)"), Alnum("D2", "X(2)"),
                 Num("C1", "9(2)"), Num("C2", "9(2)"), Num("P", "9(3)"), Num("TL", "9(2)")]
        parts = []
        for j, (d) in enumerate(dl):
            dd, is_all = d if isinstance(d, tuple) else (d, False)
            parts.append(("ALL " if is_all else "") + _lit(dd))
        delim_txt = ("DELIMITED BY " + " OR ".join(parts) + " ") if dl else ""
        if dl:
            into = "{R1} DELIMITER IN {D1} COUNT IN {C1} {R2} DELIMITER IN {D2} COUNT IN {C2} {R3}"
        else:
            into = "{R1} {R2} {R3}"
        st = (f"UNSTRING {{S}} {delim_txt}INTO {into} WITH POINTER {{P}} TALLYING IN {{TL}} "
              f'ON OVERFLOW MOVE "Y" TO SE-FLAG END-UNSTRING')

        def py(f, src=src, dl=dl, p0=p0):
            move(src, f["S"])
            for r in ("R1", "R2", "R3", "D1", "D2"):
                move("#" * f[r].size, f[r])
            move(p0, f["P"]); move(1, f["TL"])
            if dl:
                tg = [text.Into(f["R1"], f["D1"], f["C1"]), text.Into(f["R2"], f["D2"], f["C2"]), f["R3"]]
            else:
                tg = [f["R1"], f["R2"], f["R3"]]
            return text.unstring(f["S"], dl, tg, pointer=f["P"], tallying=f["TL"])

        cases.append(Case(
            "unstring_stmt", f'"{src}" {delim_txt}R1 X({rw}) POINTER {p0}', items,
            [f"MOVE {_lit(src)} TO {{S}}"] + [f'MOVE ALL "#" TO {{{r}}}' for r in ("R1", "R2", "R3", "D1", "D2")]
            + [f"MOVE {p0} TO {{P}}", "MOVE 1 TO {TL}", st],
            py, [("flag", "")] + [("hex", r) for r in ("R1", "R2", "R3", "D1", "D2", "C1", "C2", "P", "TL")]))
    return cases


INSPECT_FORMS = [
    # (COBOL phrase text, phrase builders, kind)
    ('TALLYING {C1} FOR ALL "A"', lambda f: [_P("ALL", "A", counter=f["C1"])], "T"),
    ('TALLYING {C1} FOR LEADING "A"', lambda f: [_P("LEADING", "A", counter=f["C1"])], "T"),
    ('TALLYING {C1} FOR CHARACTERS BEFORE INITIAL "B"',
     lambda f: [_P("CHARACTERS", counter=f["C1"], before="B")], "T"),
    ('TALLYING {C1} FOR ALL "AB" AFTER INITIAL " "',
     lambda f: [_P("ALL", "AB", counter=f["C1"], after=" ")], "T"),
    ('TALLYING {C1} FOR ALL "A" {C2} FOR LEADING "0"',
     lambda f: [_P("ALL", "A", counter=f["C1"]), _P("LEADING", "0", counter=f["C2"])], "T"),
    ('TALLYING {C1} FOR LEADING "0" {C2} FOR CHARACTERS',
     lambda f: [_P("LEADING", "0", counter=f["C1"]), _P("CHARACTERS", counter=f["C2"])], "T"),
    ('REPLACING ALL "A" BY "Z"', lambda f: [_P("ALL", "A", by="Z")], "R"),
    ('REPLACING LEADING "0" BY "*"', lambda f: [_P("LEADING", "0", by="*")], "R"),
    ('REPLACING FIRST "B" BY "X"', lambda f: [_P("FIRST", "B", by="X")], "R"),
    ('REPLACING CHARACTERS BY "-" BEFORE INITIAL " "', lambda f: [_P("CHARACTERS", by="-", before=" ")], "R"),
    ('REPLACING ALL "AB" BY "XY" AFTER INITIAL "0"', lambda f: [_P("ALL", "AB", by="XY", after="0")], "R"),
    ('REPLACING ALL "A" BY "1" ALL "B" BY "2"', lambda f: [_P("ALL", "A", by="1"), _P("ALL", "B", by="2")], "R"),
    ('CONVERTING "AB" TO "ba"', None, "C"),
    ('CONVERTING "A0" TO "x9" AFTER INITIAL "B"', None, "C2"),
]


def _P(mode, pattern=None, by=None, counter=None, before=None, after=None):
    from ..runtime.text import Phrase

    return Phrase(mode, pattern, by, counter, before, after)


def rule_inspect(rng, n_per_form=14):
    from ..runtime import text

    cases = []
    for form, build, kind in INSPECT_FORMS:
        for _ in range(n_per_form):
            src = _rtext(rng, "AABC0 *", rng.randint(1, 12))
            if rng.random() < 0.3:
                src = "0" * rng.randint(1, 3) + src
            items = [Alnum("X", f"X({len(src)})"), Num("C1", "9(3)"), Num("C2", "9(3)")]
            st = f"INSPECT {{X}} {form}"

            def py(f, src=src, build=build, kind=kind):
                move(src, f["X"]); move(2, f["C1"])
                if kind == "T":
                    text.inspect_tallying(f["X"], build(f))
                elif kind == "R":
                    text.inspect_replacing(f["X"], build(f))
                elif kind == "C":
                    text.inspect_converting(f["X"], "AB", "ba")
                else:
                    text.inspect_converting(f["X"], "A0", "x9", after="B")
                return False

            cases.append(Case(
                "inspect_stmt", f'"{src}" {form.replace("{", "").replace("}", "")}', items,
                [f"MOVE {_lit(src)} TO {{X}}", "MOVE 2 TO {C1}", st],
                py, [("hex", "X"), ("hex", "C1"), ("hex", "C2")]))
    return cases


RULES.update({
    "string_stmt": rule_string,
    "unstring_stmt": rule_unstring,
    "inspect_stmt": rule_inspect,
})


# ---- rules added after independent review --------------------------------

def rule_literal_truncation(rng):
    """Numeric literals with more decimal places than the receiver."""
    cases = []
    vals = ["-0.004", "0.004", "-0.005", "-1.239", "1.239", "-0.0001", "-12.3456", "9.999"]
    for pic in ("S9V99", "9V99", "S9(3)V9", "S9(3)", "S99V9(3)"):
        ip = parse_pic(pic).digits - parse_pic(pic).scale
        for u in USAGES:
            for v in vals:
                if abs(Decimal(v)) >= 10 ** ip:
                    continue  # high-order overflow of literals is refused (encode_literal)
                t = Num("T", pic, usage=u)
                cases.append(Case(
                    "literal_truncation", f"MOVE {v} TO {fmt_item(t)}", [t],
                    [f"MOVE {v} TO {{T}}"], (lambda f, v=v: move(Decimal(v), f["T"])), [("hex", "T")]))
        for epic in ("ZZ9.99-", "Z9.9+", "ZZ9.99CR"):
            for v in vals:
                t = Edited("T", epic)
                cases.append(Case(
                    "literal_truncation", f"MOVE {v} TO {epic}", [t],
                    [f"MOVE {v} TO {{T}}"], (lambda f, v=v: move(Decimal(v), f["T"])), [("hex", "T")]))
    return cases


def rule_edit_trailing_sign(rng):
    """Editing where the sender has more decimal places than the receiver."""
    cases = []
    pics = ["ZZZ9-", "999+", "ZZ9.99-", "ZZZ-", "***-", "ZZZ+", "ZZ9.9+", "ZZZ9CR", "-ZZ9", "---9"]
    vals = ["-0.5", "0.5", "-0.004", "0.004", "-0.05", "-1.5", "12.345", "-12.345", "0", "-0.009"]
    for sp in ("S9(5)V9(3)", "S9(3)V9"):
        for su in (enc.DISPLAY, enc.COMP3, enc.COMP):
            for pic in pics:
                for v in vals:
                    s, t = Num("S", sp, usage=su), Edited("T", pic)
                    q = parse_pic(sp).scale
                    if len(v.split(".")[-1]) > q and "." in v:
                        continue
                    cases.append(Case(
                        "edit_trailing_sign", f"{v} {fmt_item(s)} -> {pic}", [s, t],
                        [f"MOVE {v} TO {{S}}", "MOVE {S} TO {T}"],
                        (lambda f, v=v: (move(Decimal(v), f["S"]), move(f["S"], f["T"]))),
                        [("hex", "T")]))
    return cases


def rule_arith_single(rng):
    """ADD / SUBTRACT with one operand (literal or item), the form GnuCOBOL
    compiles to its integer fast path when the operand is a small integer."""
    cases = []
    targets = [("9(4)", enc.COMP5), ("S9(4)", enc.COMP5), ("9(4)", enc.COMP3), ("S9(4)", enc.COMP3),
               ("9(3)", enc.COMP3), ("9(4)", enc.DISPLAY), ("S9(4)", enc.DISPLAY), ("9(4)", enc.COMP),
               ("S9(3)V9", enc.COMP3), ("9(2)", enc.COMP5)]
    operands = [("lit", None, "1"), ("lit", None, "9999"), ("lit", None, "123456789"),
                ("lit", None, "1234567890"), ("lit", None, "0.5"),
                ("item", "9", "1"), ("item", "9(9)", "999999999"), ("item", "9(10)", "1"),
                ("item", "S9(4)", "-2"), ("item", "9V9", "1.0")]
    starts = ["0", "1", "9999", "9998", "5"]
    for tp, tu in targets:
        for kind, opic, oval in operands:
            for verb in ("ADD", "SUBTRACT"):
                for se in (False, True):
                    tv = pick(rng, starts)
                    t = Num("T", tp, usage=tu)
                    if Decimal(tv) >= 10 ** (parse_pic(tp).digits - parse_pic(tp).scale):
                        tv = "1"
                    items = [t]
                    if kind == "item":
                        o = Num("O", opic)
                        items.append(o)
                        src = "{O}"
                    else:
                        src = oval
                    st = f"ADD {src} TO {{T}}" if verb == "ADD" else f"SUBTRACT {src} FROM {{T}}"
                    if se:
                        st += f' ON SIZE ERROR MOVE "Y" TO SE-FLAG END-{verb}'
                    cob = [f"MOVE {tv} TO {{T}}"] + ([f"MOVE {oval} TO {{O}}"] if kind == "item" else []) + [st]

                    def py(f, tv=tv, kind=kind, oval=oval, verb=verb, se=se):
                        move(Decimal(tv), f["T"])
                        if kind == "item":
                            move(Decimal(oval), f["O"])
                            op = f["O"]
                        else:
                            op = Decimal(oval)
                        fn = arith.add if verb == "ADD" else arith.subtract
                        return fn(op, f["T"], on_size_error=se) and se

                    cases.append(Case(
                        "arith_single_operand",
                        f"{verb} {oval}{' ' + opic if opic else ''} {'TO' if verb == 'ADD' else 'FROM'} "
                        f"{tv} {fmt_item(t)}{' SIZE-ERROR' if se else ''}",
                        items, cob, py, [("flag", ""), ("hex", "T")]))
    return cases


def rule_figurative_group(rng):
    from ..runtime.move import HIGH_VALUES, LOW_VALUES, SPACES, ZEROS, All, initialize
    from ..runtime.storage import Group

    cases = []
    figs = [("SPACES", SPACES), ("ZEROS", ZEROS), ("HIGH-VALUES", HIGH_VALUES),
            ("LOW-VALUES", LOW_VALUES), ('ALL "AB"', All("AB")), ('ALL "*"', All("*"))]
    for name, fig in figs:
        for pic in ("X(5)", "X", "X(12)"):
            t = Alnum("T", pic)
            cases.append(Case("figurative_group", f"MOVE {name} TO {pic}", [t], [f"MOVE {name} TO {{T}}"],
                              (lambda f, fig=fig: move(fig, f["T"])), [("hex", "T")]))
    for pic in ("S9(3)V99", "9(4)", "ZZ9.99"):
        for u in (USAGES if parse_pic(pic).category == NUMERIC else [enc.DISPLAY]):
            t = Num("T", pic, usage=u) if parse_pic(pic).category == NUMERIC else Edited("T", pic)
            cases.append(Case("figurative_group", f"MOVE ZEROS TO {fmt_item(t)}", [t],
                              ["MOVE 5 TO {T}", "MOVE ZEROS TO {T}"],
                              (lambda f: (move(5, f["T"]), move(ZEROS, f["T"]))), [("hex", "T")]))

    def grp(name):
        return Group(name, [Alnum(name + "A", "X(3)"), Num(name + "N", "S9(3)V9", usage=enc.COMP3),
                            Num(name + "D", "S99"), Group(name + "T", [Num(name + "E", "9")], occurs=3)])

    # group to group, group to elementary, elementary to group
    for txt in ("ABC", "1234567890", ""):
        s = Alnum("S", "X(12)")
        g = grp("G")
        lit = _lit(txt) if txt else "SPACES"
        cases.append(Case("figurative_group", f"MOVE {lit} X(12) TO group", [s, g],
                          [f"MOVE {lit} TO {{S}}", "MOVE {S} TO {G}"],
                          (lambda f, txt=txt: (move(txt or SPACES, f["S"]), move(f["S"], f["G"]))),
                          [("hex", "G")]))
    g1, g2 = grp("H"), grp("K")
    cases.append(Case("figurative_group", "MOVE group TO group, INITIALIZE, OCCURS subscripts",
                      [g1, g2],
                      ['MOVE "XYZ" TO {H}A', "MOVE -12.5 TO {H}N", "MOVE -7 TO {H}D",
                       "MOVE 4 TO {H}E(2)", "MOVE {H} TO {K}", "INITIALIZE {H}"],
                      None, [("hex", "H"), ("hex", "K")]))

    def py_group(f):
        st = f["_storage"]
        move("XYZ", st["HA"]); move(Decimal("-12.5"), st["HN"]); move(-7, st["HD"])
        move(4, st.f("HE", 2)); move(st["H"], st["K"]); initialize(st["H"])

    cases[-1].py = py_group
    return cases


INSPECT_FORMS.extend([
    ('TALLYING {C1} FOR ALL "BC" {C2} FOR ALL "AB"',
     lambda f: [_P("ALL", "BC", counter=f["C1"]), _P("ALL", "AB", counter=f["C2"])], "T"),
    ('TALLYING {C1} FOR LEADING "A" {C2} FOR ALL "AA"',
     lambda f: [_P("LEADING", "A", counter=f["C1"]), _P("ALL", "AA", counter=f["C2"])], "T"),
    ('TALLYING {C1} FOR ALL "AA" {C2} FOR LEADING "A"',
     lambda f: [_P("ALL", "AA", counter=f["C1"]), _P("LEADING", "A", counter=f["C2"])], "T"),
    ('REPLACING ALL "BC" BY "xy" ALL "AB" BY "pq"',
     lambda f: [_P("ALL", "BC", by="xy"), _P("ALL", "AB", by="pq")], "R"),
    ('REPLACING FIRST "AB" BY "12" CHARACTERS BY "-" AFTER INITIAL "B"',
     lambda f: [_P("FIRST", "AB", by="12"), _P("CHARACTERS", by="-", after="B")], "R"),
])

RULES.update({
    "literal_truncation": rule_literal_truncation,
    "edit_trailing_sign": rule_edit_trailing_sign,
    "arith_single_operand": rule_arith_single,
    "figurative_group": rule_figurative_group,
})


def rule_value_clause(rng):
    """VALUE clauses, checked through the item's initial bytes."""
    from ..runtime.move import HIGH_VALUES, SPACES, ZEROS, All

    cases = []
    vals = [("ZERO", ZEROS), ("SPACES", SPACES), ('ALL "*"', All("*")), ("HIGH-VALUES", HIGH_VALUES),
            ('"  5.00"', "  5.00"), ('"AB"', "AB"), ("5", Decimal(5)), ("-12.5", Decimal("-12.5")),
            ("0", Decimal(0))]
    for pic in ("ZZ9.99", "$$$9.99", "***.**", "ZZ9.99-", "X(6)", "S9(3)V99", "9(4)"):
        cat = parse_pic(pic).category
        for cob, py_val in vals:
            numeric_lit = isinstance(py_val, Decimal)
            if cat == NUMERIC and not (numeric_lit or py_val is ZEROS):
                continue
            if cat in ("alphanumeric",) and numeric_lit:
                continue
            if numeric_lit and py_val < 0 and not parse_pic(pic).signed:
                continue  # cobc rejects a negative VALUE for an unsigned item
            mk = {"numeric": Num, "numeric-edited": Edited}.get(cat, Alnum)
            t = mk("T", pic, value=py_val)
            cases.append(Case("value_clause", f"{pic} VALUE {cob}", [t], [],
                              lambda f: None, [("hex", "T")]))
    return cases


RULES["value_clause"] = rule_value_clause


# ---- rules added for the GnuCOBOL 3.1.2 / 3.2 comparison --------------------

def rule_rounded_single(rng):
    """ADD x TO y ROUNDED / SUBTRACT x FROM y ROUNDED with one operand that has
    more decimal places than the receiver. GnuCOBOL ticket #934 reports that
    3.2 drops the default ROUNDED mode when the receiver is COMP-3."""
    cases = []
    targets = [("S9(5)V99", enc.COMP3), ("S9(4)V9", enc.COMP3), ("9(5)V99", enc.COMP3),
               ("S9(5)V99", enc.DISPLAY), ("S9(5)V99", enc.COMP)]
    operands = [("S9V999", "0.005"), ("S9V999", "-0.005"), ("S9V999", "0.015"), ("S9V999", "1.235"),
                ("S99V9(4)", "12.3450"), ("S99V9(4)", "-0.0450"), ("9V9", "0.5"), ("S9V999", "0.004")]
    for tp, tu in targets:
        for opic, oval in operands:
            if Decimal(oval) < 0 and not parse_pic(opic).signed:
                continue
            for verb in ("ADD", "SUBTRACT"):
                for se in (False, True):
                    tv = "1.00" if parse_pic(tp).scale == 2 else "1.0"
                    t, o = Num("T", tp, usage=tu), Num("O", opic)
                    st = f"ADD {{O}} TO {{T}} ROUNDED" if verb == "ADD" else f"SUBTRACT {{O}} FROM {{T}} ROUNDED"
                    if se:
                        st += f' ON SIZE ERROR MOVE "Y" TO SE-FLAG END-{verb}'

                    def py(f, tv=tv, oval=oval, verb=verb, se=se):
                        move(Decimal(tv), f["T"]); move(Decimal(oval), f["O"])
                        fn = arith.add if verb == "ADD" else arith.subtract
                        return fn(f["O"], f["T"], rounded=True, on_size_error=se) and se

                    cases.append(Case(
                        "arith_rounded_single_operand",
                        f"{verb} {oval} {opic} {'TO' if verb == 'ADD' else 'FROM'} {tv} {fmt_item(t)} ROUNDED"
                        f"{' SIZE-ERROR' if se else ''}",
                        [t, o], [f"MOVE {tv} TO {{T}}", f"MOVE {oval} TO {{O}}", st], py,
                        [("flag", ""), ("hex", "T")]))
    return cases


def rule_inspect_iso_example(rng):
    """The INSPECT TALLYING example that GnuCOBOL ticket #991 quotes from
    ISO/IEC 1989:2023 appendix D.25 (the ticket gives 03 01 01 00 05 as the
    expected counts). We have not read the standard text itself."""
    from ..runtime import text

    items = [Alnum("X", "X(14)")] + [Num(f"C{k}", "99") for k in range(5)]

    def py(f):
        move("EFABDBCGABEFGG", f["X"])
        text.inspect_tallying(f["X"], [
            _P("ALL", "AB", counter=f["C0"]), _P("ALL", "D", counter=f["C0"]),
            _P("ALL", "BC", counter=f["C1"]), _P("LEADING", "EF", counter=f["C2"]),
            _P("LEADING", "B", counter=f["C3"]), _P("CHARACTERS", counter=f["C4"])])
        return False

    return [Case(
        "inspect_iso_example", 'ticket #991 / ISO D.25: "EFABDBCGABEFGG"', items,
        ['MOVE "EFABDBCGABEFGG" TO {X}',
         'INSPECT {X} TALLYING {C0} FOR ALL "AB" ALL "D" {C1} FOR ALL "BC" '
         '{C2} FOR LEADING "EF" {C3} FOR LEADING "B" {C4} FOR CHARACTERS'],
        py, [("hex", f"C{k}") for k in range(5)])]


RULES.update({
    "arith_rounded_single_operand": rule_rounded_single,
    "inspect_iso_example": rule_inspect_iso_example,
})

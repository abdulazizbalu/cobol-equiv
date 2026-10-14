"""Numeric comparison: CobDecimal (==, !=, <, <=, >, >=) vs GnuCOBOL IF.

Pairs of values are moved through a wide DISPLAY item into items of
different PICTUREs, scales, signs and usages (negative zero included,
semantic trap 6); for each pair the program displays one letter per
relation of IF A rel B and of IF A * 2 rel B + 1 (an arithmetic expression
on both sides). The runtime computes the same letters with the six
operators on dec(a) and dec(b). test_value_semantics covers int and
Decimal operands, hashing and the operands that are not compared."""

import operator
import random
import subprocess
from decimal import Decimal

import pytest

from cobol_equiv.cobc import COBC_FLAGS, clean_env, cobc_path
from cobol_equiv.runtime import COMP, COMP3, Num, Storage, dec, move

ITEMS = [("A", "S9(4)V99", "DISPLAY"), ("B", "S9(3)V9(3)", "COMP-3"), ("C", "S9(6)", "COMP"),
         ("D", "9(3)V9", "DISPLAY")]
USAGE = {"DISPLAY": None, "COMP-3": COMP3, "COMP": COMP}
RELS = [("=", operator.eq), ("NOT =", operator.ne), ("<", operator.lt), ("<=", operator.le), (">", operator.gt),
        (">=", operator.ge)]
EXPR = {"A": "A * 2", "B": "B + 1"}


def values():
    rnd = random.Random(20261014)
    fixed = ["0", "-0", "-10000", "1.5", "1.50", "-1.5", "999.999", "-999.999", "0.001", "-0.001",
             "12", "12.0", "-12", "100.5", "2.25", "5.5"]
    return fixed + [f"{rnd.randint(-99999, 99999) / 100:.2f}" for _ in range(24)]


def pairs():
    rnd = random.Random(7)
    vs = values()
    out = [(x, y) for x in vs[:16] for y in vs[:16]]
    out += [(rnd.choice(vs), rnd.choice(vs)) for _ in range(120)]
    return [(left, right, x, y) for x, y in out
            for left, right in (("A", "B"), ("C", "A"), ("B", "D"))]


def cobol(cases):
    lines = []
    for left, right, x, y in cases:
        lines += [f"           MOVE {x} TO W", f"           MOVE W TO {left}",
                  f"           MOVE {y} TO W", f"           MOVE W TO {right}"]
        for i, (rel, _) in enumerate(RELS):
            lines += [f"           MOVE 'n' TO R({i + 1})",
                      f"           IF {left} {rel} {right} MOVE 'y' TO R({i + 1}) END-IF"]
        lines += [f"           MOVE 'n' TO R({7 + i})" for i in range(6)]
        for i, (rel, _) in enumerate(RELS):
            lines.append(f"           IF {left} * 2 {rel} {right} + 1 MOVE 'y' TO R({7 + i}) END-IF")
        lines.append("           DISPLAY RS")
    decl = "".join(f"       01 {n} PIC {p}{'' if u == 'DISPLAY' else ' ' + u}.\n" for n, p, u in ITEMS)
    return ("       IDENTIFICATION DIVISION.\n       PROGRAM-ID. CMPR.\n       DATA DIVISION.\n"
            "       WORKING-STORAGE SECTION.\n" + decl + "       01 W PIC S9(6)V9(3).\n" +
            "       01 RS.\n          05 R PIC X OCCURS 12.\n       PROCEDURE DIVISION.\n"
            + "\n".join(lines) + "\n           STOP RUN.\n")


def python_lines(cases) -> tuple[bytes, int]:
    items = [Num(n, p, usage=USAGE[u]) if USAGE[u] else Num(n, p) for n, p, u in ITEMS]
    ws = Storage("WS", items + [Num("W", "S9(6)V9(3)")])
    out, negative_zeros = b"", 0
    for left, right, x, y in cases:
        move(Decimal(x), ws["W"])
        move(ws["W"], ws[left])
        move(Decimal(y), ws["W"])
        move(ws["W"], ws[right])
        negative_zeros += sum(ws[n].sign_mag() == (True, 0) for n in (left, right))
        a, b = dec(ws[left]), dec(ws[right])
        ea, eb = a * 2, b + 1
        res = [op(a, b) for _, op in RELS] + [op(ea, eb) for _, op in RELS]
        out += "".join("y" if r else "n" for r in res).encode("ascii") + b"\n"
    return out, negative_zeros


@pytest.mark.oracle
def test_comparisons_match_gnucobol(tmp_path):
    cases = pairs()
    src = tmp_path / "cmpr.cob"
    src.write_text(cobol(cases), encoding="utf-8")
    exe = tmp_path / "cmpr"
    r = subprocess.run([cobc_path(), *COBC_FLAGS, "-o", str(exe), str(src)],
                       capture_output=True, env=clean_env())
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    out = subprocess.run([str(exe)], cwd=tmp_path, capture_output=True, env=clean_env())
    assert out.returncode == 0, out.stderr
    expected = out.stdout.splitlines()
    text, negative_zeros = python_lines(cases)
    actual = text.splitlines()
    assert len(expected) == len(cases)
    bad = [(c, e, a) for c, e, a in zip(cases, expected, actual) if e != a]
    assert not bad, f"{len(bad)} of {len(cases)} differ, first: {bad[:3]}"
    # the pairs include equal values and operands holding negative zero
    assert any(line.startswith(b"y") for line in expected) and negative_zeros > 0


def test_value_semantics():
    assert dec("1.50") == dec("1.5") and hash(dec("1.50")) == hash(dec("1.5"))
    assert dec(0) == -dec(0) == dec("0.000")
    assert dec(3) == 3 and 3 == dec(3) and dec("2.5") == Decimal("2.50")
    assert hash(dec(3)) == hash(3) and hash(dec("2.50")) == hash(Decimal("2.5"))
    assert dec("-1") < dec("0.001") <= dec("0.0010") < 1 and dec(7) > Decimal("6.99")
    assert dec(1) != dec("1.01") and not (dec(1) != dec("1.000"))
    assert len({dec(1), dec("1.0"), 1, Decimal("1.00"), dec(2)}) == 2
    assert {dec("0.5"): "x"}[dec("0.50")] == "x"
    a, b = dec(9) / dec(3), dec(3)
    assert a == b  # 3.000... (38 places) equals 3
    # operands that are not compared
    assert dec(1) != "1" and not (dec(1) == "1") and dec(1) != 1.0 and dec(1) != True  # noqa: E712
    with pytest.raises(TypeError):
        dec(1) < "2"  # noqa: B015
    with pytest.raises(ArithmeticError):
        dec(1) / 0 == dec(1)  # noqa: B015
    with pytest.raises(ArithmeticError):
        hash(dec(1) / 0)

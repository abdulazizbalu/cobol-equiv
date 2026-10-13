"""Reference modification: runtime (refmod) vs GnuCOBOL.

A list of MOVEs between reference-modified alphanumeric and numeric
DISPLAY items, with constant and variable start and length; after each
MOVE the whole group is displayed."""

import random
import subprocess

import pytest

from cobol_equiv.cobc import COBC_FLAGS, clean_env, cobc_path
from cobol_equiv.runtime import Alnum, Num, Storage, display_line, move, refmod

ITEMS = [Alnum("A", "X(10)", value="ABCDEFGHIJ"), Alnum("B", "X(8)", value="12345678"),
         Num("N", "9(6)", value=123456), Num("M", "9(4)", value=0)]
SIZES = {"A": 10, "B": 8, "N": 6, "M": 4}


def cases():
    rnd = random.Random(20261013)
    out = []
    for _ in range(60):
        s, d = rnd.choice("ABN"), rnd.choice("ABNM")
        ss = rnd.randint(1, SIZES[s])
        sl = rnd.randint(1, SIZES[s] - ss + 1)
        ds = rnd.randint(1, SIZES[d])
        dl = rnd.choice([None, rnd.randint(1, SIZES[d] - ds + 1)])
        out.append((s, ss, sl, d, ds, dl))
    out.append(("A", 1, 10, "M", 1, None))  # receiver from start to end
    return out


def cobol(cases_):
    lines = []
    for s, ss, sl, d, ds, dl in cases_:
        recv = f"{d}(I:)" if dl is None else f"{d}(I:J)"
        lines += [f"           MOVE {ds} TO I", f"           MOVE {dl or 0} TO J",
                  f"           MOVE {s}({ss}:{sl}) TO {recv}", "           DISPLAY G"]
    return ("       IDENTIFICATION DIVISION.\n       PROGRAM-ID. RM.\n       DATA DIVISION.\n"
            "       WORKING-STORAGE SECTION.\n       01 G.\n"
            '          05 A PIC X(10) VALUE "ABCDEFGHIJ".\n          05 B PIC X(8) VALUE "12345678".\n'
            "          05 N PIC 9(6) VALUE 123456.\n          05 M PIC 9(4) VALUE 0.\n"
            "       01 I PIC 99.\n       01 J PIC 99.\n       PROCEDURE DIVISION.\n"
            + "\n".join(lines) + "\n           STOP RUN.\n")


@pytest.mark.oracle
def test_refmod_matches_gnucobol(tmp_path):
    cs = cases()
    src = tmp_path / "rm.cob"
    src.write_text(cobol(cs), encoding="utf-8")
    exe = tmp_path / "rm"
    r = subprocess.run([cobc_path(), *COBC_FLAGS, "-o", str(exe), str(src)],
                       capture_output=True, env=clean_env())
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    out = subprocess.run([str(exe)], cwd=tmp_path, capture_output=True, env=clean_env())
    assert out.returncode == 0, out.stderr

    from cobol_equiv.runtime import Group
    ws = Storage("WS", [Group("G", ITEMS)])
    expected = b""
    for s, ss, sl, d, ds, dl in cs:
        move(refmod(ws[s], ss, sl), refmod(ws[d], ds, dl))
        expected += display_line(ws["G"])
    assert out.stdout == expected

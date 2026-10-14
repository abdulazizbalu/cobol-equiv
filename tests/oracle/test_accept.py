"""ACCEPT from standard input: runtime (runtime/accept.py) vs GnuCOBOL.

Each round ACCEPTs one line into each of six items and dumps the raw bytes
of all of them in hex; the input runs past its end, so the end-of-input
behaviour is covered too."""

import subprocess

import pytest

from cobol_equiv.cobc import COBC_FLAGS, clean_env, cobc_path
from cobol_equiv.runtime import COMP3, Alnum, Edited, Num, Stdin, Storage

ITEMS = [Num("N", "S9(5)"), Num("U", "9(3)V99"), Alnum("X", "X(5)"),
         Num("K", "9(3)", usage=COMP3), Num("P", "S9(3)V9", usage=COMP3), Edited("E", "-(4)9.99")]

PROG = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. ACC.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 G.
          05 N PIC S9(5).
          05 U PIC 9(3)V99.
          05 X PIC X(5).
          05 K PIC 9(3) COMP-3.
          05 P PIC S9(3)V9 COMP-3.
          05 E PIC -(4)9.99.
       01 HEXD PIC X(16) VALUE "0123456789ABCDEF".
       01 I PIC 9(4) COMP.
       01 B PIC 9(4) COMP.
       01 R PIC 99.
       01 H1 PIC 99.
       01 H2 PIC 99.
       PROCEDURE DIVISION.
           PERFORM VARYING R FROM 1 BY 1 UNTIL R > ROUNDS
             ACCEPT N ACCEPT U ACCEPT X ACCEPT K ACCEPT P ACCEPT E
             PERFORM VARYING I FROM 1 BY 1 UNTIL I > LENGTH OF G
               COMPUTE B = FUNCTION ORD(G(I:1)) - 1
               DIVIDE B BY 16 GIVING H1 REMAINDER H2
               ADD 1 TO H1 H2
               DISPLAY HEXD(H1:1) HEXD(H2:1) WITH NO ADVANCING
             END-PERFORM
             DISPLAY " "
           END-PERFORM
           STOP RUN.
"""

LINES = [b"-123", b"12.5", b"ab", b"7", b"-4.56", b"1,234.5",
         b"12", b"-1.239", b"abcdefg", b"-5", b"999.95", b"x",
         b"abc", b"1,5", b"  x", b" 9 9", b"+12.34", b"-0",
         b" 42 ", b"+3", b"", b"", b"", b"",
         b"1x2", b"9999.99", b"\tz", b"1234", b"12345", b"1.2.3",
         b"123456", b"0.005", b"Z", b"abc", b"-0", b"77"]


@pytest.mark.oracle
def test_accept_matches_gnucobol(tmp_path):
    rounds = len(LINES) // 6 + 2  # two rounds past the end of the input
    src = tmp_path / "acc.cob"
    src.write_text(PROG.replace("ROUNDS", str(rounds)), encoding="utf-8")
    exe = tmp_path / "acc"
    r = subprocess.run([cobc_path(), *COBC_FLAGS, "-o", str(exe), str(src)],
                       capture_output=True, env=clean_env())
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    stdin = b"".join(line + b"\n" for line in LINES)
    out = subprocess.run([str(exe)], input=stdin, cwd=tmp_path, capture_output=True, env=clean_env())
    assert out.returncode == 0, out.stderr

    ws = Storage("G", ITEMS)
    inp = Stdin(stdin)
    expected = b""
    for _ in range(rounds):
        for name in "NUXKPE":
            inp.accept(ws[name])
        expected += bytes(ws.area).hex().upper().encode() + b" \n"
    assert out.stdout == expected

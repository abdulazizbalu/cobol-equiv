"""GnuCOBOL behaviours that the runtime deliberately refuses to model or that
deviate from the COBOL standard. Each test pins what GnuCOBOL 3.1.2 actually
does, so docs/semantic-traps.md can cite it."""

import subprocess
from decimal import Decimal

import pytest

from cobol_equiv.cobc import COBC_FLAGS, clean_env, cobc_path
from cobol_equiv.runtime import COMP, Edited, Num, Storage, move
from cobol_equiv.runtime.errors import Unsupported

HEAD = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. Q.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
"""


def run_cobol(tmp_path, data: str, proc: str) -> bytes:
    src = tmp_path / "q.cob"
    src.write_text(HEAD + data + "       PROCEDURE DIVISION.\n" + proc + "           STOP RUN.\n",
                   encoding="utf-8")
    exe = tmp_path / "q"
    subprocess.run([cobc_path(), *COBC_FLAGS, "-o", str(exe), str(src)],
                   check=True, capture_output=True, env=clean_env())
    return subprocess.run([str(exe)], check=True, capture_output=True, env=clean_env()).stdout


@pytest.mark.oracle
def test_fixed_minus_with_floating_currency_prints_minus_for_positive(tmp_path):
    out = run_cobol(tmp_path,
                    "       01 S PIC S9(5)V99 VALUE 5.\n       01 E PIC -$$$9.99.\n",
                    "           MOVE S TO E\n           DISPLAY E\n")
    assert out == b"-  $5.00\n"  # the standard would give "   $5.00"
    with pytest.raises(Unsupported):
        Storage("W", [Edited("E", "-$$$9.99")])


@pytest.mark.oracle
def test_huge_value_into_comp_is_not_decimal_truncation(tmp_path):
    out = run_cobol(tmp_path,
                    "       01 S PIC S9(31) VALUE -1000000000000000000000000000000.\n"
                    "       01 T PIC S9(18) COMP.\n",
                    "           MOVE S TO T\n           DISPLAY T\n")
    # decimal high-order truncation would give zero
    assert out != b"+000000000000000000\n"
    st = Storage("W", [Num("S", "S9(31)"), Num("T", "S9(18)", usage=COMP)])
    move(Decimal("-1000000000000000000000000000000"), st["S"])
    with pytest.raises(Unsupported):
        move(st["S"], st["T"])


@pytest.mark.oracle
def test_remainder_stored_despite_quotient_size_error(tmp_path):
    out = run_cobol(tmp_path,
                    "       01 A PIC S9(5) VALUE 12345.\n       01 B PIC S9(3) VALUE 10.\n"
                    "       01 Q PIC S9(2) VALUE 7.\n       01 R PIC S9(3) VALUE 9.\n",
                    "           DIVIDE A BY B GIVING Q REMAINDER R\n"
                    "             ON SIZE ERROR DISPLAY \"SIZE ERROR\"\n"
                    "           END-DIVIDE\n           DISPLAY Q \" \" R\n")
    # quotient 1234 does not fit S9(2): Q unchanged, but R is still set to 5
    assert out == b"SIZE ERROR\n+07 +005\n"
    from cobol_equiv.runtime import divide_remainder

    st = Storage("W", [Num("A", "S9(5)", value=12345), Num("B", "S9(3)", value=10),
                       Num("Q", "S9(2)", value=7), Num("R", "S9(3)", value=9)])
    assert divide_remainder(st["A"], st["B"], st["Q"], st["R"], on_size_error=True)
    assert (st["Q"].value, st["R"].value) == (7, 5)

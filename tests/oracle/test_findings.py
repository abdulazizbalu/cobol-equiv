"""Each documented GnuCOBOL finding, reproduced with a small program on the
compiler under test. Expected output is recorded per version; a version not
listed here fails the test, so a new compiler has to be looked at before its
results are trusted. See docs/findings.md."""

import subprocess
from pathlib import Path

import pytest

from cobol_equiv.cobc import COBC_FLAGS, clean_env, cobc_path, version_label

HERE = Path(__file__).parent / "findings"

SAME = object()  # marker: same as 3.1.2

EXPECTED = {
    "neg_zero": {
        "3.1.2": (0, "MOVE-DISPLAY [000p] +0000\nADD-COMP3 x'00000D' +00000\n"
                     "ADD-DISPLAY [000p] +0000\nD-EQUALS-ZERO\n"),
        "3.2": SAME,
    },
    "comp5": {
        "3.1.2": (0, "MOVE 99999 COMP-5 -31073 COMP +9999\nADD -32768 SIZE ERROR\nB5 +00000\n"
                     "ADD 12345 OK\nB5 +12345\n"),
        "3.2": SAME,
    },
    "remainder": {
        "3.1.2": (0, "SIZE ERROR\nQ +07 R +005\n"),
        "3.2": SAME,
    },
    "fastpath": {
        "3.1.2": (0, "SUBTRACT 1 FROM 0 9(4) COMP-5: 65535\nADD 1 TO 9999 9(4) COMP-3: x'10000F'\n"),
        "3.2": SAME,
    },
    "edit_minus": {
        "3.1.2": (0, "+5    [-  $5.00]\n-5    [-  $5.00]\n+1000 [ 1000.00]\n"),
        "3.2": SAME,
    },
    "inspect": {
        "3.1.2": (0, "TALLY BC/AB 02 00\nREPLACE AxyAxy\nLEADING/CHARACTERS 04 00\n"),
        "3.2": (0, "TALLY BC/AB 02 00\nREPLACE AxyAxy\nLEADING/CHARACTERS 04 01\n"),
    },
    "inspect_twice": {
        "3.1.2": (0, "001 001\n001 001\n"),
        # the second INSPECT aborts with "attempt to reference invalid memory address"
        "3.2": ("nonzero", "001 001\n"),
    },
    "rounded_comp3": {
        "3.1.2": (0, "COMP-3 +00001.01 DISPLAY +00001.01\n"),
        "3.2": (0, "COMP-3 +00001.00 DISPLAY +00001.01\n"),
    },
    "huge_comp": {
        "3.1.2": (0, "-076944270305263616\n"),  # not a decimal truncation
        "3.2": (0, "+000000000000000000\n"),    # decimal truncation
    },
    "move_packed_sign": {
        "3.1.2": (0, "x'051C'\nNUMERIC\n"),
        "3.2": (0, "x'051F'\nNOT NUMERIC\n"),
    },
}


def expected_for(name: str, version: str):
    table = EXPECTED[name]
    if version not in table:
        pytest.fail(f"no recorded expectation for GnuCOBOL {version}: check docs/findings.md")
    exp = table[version]
    return table["3.1.2"] if exp is SAME else exp


@pytest.mark.oracle
@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_finding(tmp_path, name):
    exe = tmp_path / name
    r = subprocess.run([cobc_path(), *COBC_FLAGS, "-o", str(exe), str(HERE / f"{name}.cob")],
                       capture_output=True, env=clean_env())
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    out = subprocess.run([str(exe)], capture_output=True, env=clean_env(), timeout=30)
    rc, stdout = expected_for(name, version_label())
    if rc == "nonzero":
        assert out.returncode != 0
        assert out.stdout.decode("latin-1").startswith(stdout)
    else:
        assert out.returncode == rc
        assert out.stdout.decode("latin-1") == stdout


# ---- what the runtime does with the same constructs (no cobc needed) ----------

def test_runtime_refuses_or_models_each_finding():
    from decimal import Decimal

    from cobol_equiv.runtime import (COMP, COMP3, COMP5, Edited, Num, Storage, add,
                                     divide_remainder, move, subtract)
    from cobol_equiv.runtime.errors import Unsupported

    # neg_zero, comp5, remainder: modelled (3.1.2 behaviour)
    st = Storage("W", [Num("S", "S9(6)", value=-10000), Num("D", "S9(4)")])
    move(st["S"], st["D"])
    assert st["D"].raw == b"000p"
    st = Storage("W", [Num("A", "S9(5)", value=12345), Num("B", "S9(3)", value=10),
                       Num("Q", "S9(2)", value=7), Num("R", "S9(3)", value=9)])
    assert divide_remainder(st["A"], st["B"], st["Q"], st["R"], on_size_error=True)
    assert (st["Q"].value, st["R"].value) == (7, 5)
    # fastpath, edit_minus, huge_comp: refused
    st = Storage("W", [Num("U", "9(4)", usage=COMP5, value=0), Num("P", "9(4)", usage=COMP3, value=9999)])
    with pytest.raises(Unsupported):
        subtract(1, st["U"])
    with pytest.raises(Unsupported):
        add(1, st["P"])
    with pytest.raises(Unsupported):
        Storage("W", [Edited("E", "-$$$9.99")])
    st = Storage("W", [Num("S", "S9(31)"), Num("T", "S9(18)", usage=COMP)])
    move(Decimal("-1000000000000000000000000000000"), st["S"])
    with pytest.raises(Unsupported):
        move(st["S"], st["T"])

"""Pure-Python unit tests of the runtime (no GnuCOBOL needed).

Expected values here were taken from GnuCOBOL 3.1.2 runs (oracle cases);
the oracle tests in tests/oracle re-check them against cobc.
"""

from decimal import Decimal

import pytest

from cobol_equiv.runtime import (COMP, COMP3, COMP5, Alnum, CobDecimal, Edited, Group, Num,
                                 PicError, SPACES, Storage, ZEROS, add, compute, dec,
                                 display_line, divide_remainder, move, parse_pic)
from cobol_equiv.runtime.errors import Unsupported
from cobol_equiv.runtime.move import MoveError


def one(item):
    st = Storage("T", [item])
    return st[item.name]


def test_pic_parse():
    p = parse_pic("S9(5)V99")
    assert (p.category, p.digits, p.scale, p.signed, p.size) == ("numeric", 7, 2, True, 7)
    e = parse_pic("$$$,$$9.99CR")
    assert (e.category, e.digits, e.scale, e.size) == ("numeric-edited", 7, 2, 12)
    assert parse_pic("X(10)").size == 10
    with pytest.raises(PicError):
        parse_pic("9(3)P")
    with pytest.raises(PicError):
        parse_pic("9S9")


@pytest.mark.parametrize("pic,usage,size", [
    ("9(4)", "DISPLAY", 4), ("S9(5)V99", COMP3, 4), ("9(2)", COMP, 1), ("9(4)", COMP, 2),
    ("S9(9)", COMP5, 4), ("9(18)", COMP, 8), ("S9(4)", COMP3, 3),
])
def test_storage_sizes(pic, usage, size):
    assert one(Num("X", pic, usage=usage)).size == size


def test_overpunch_and_packed_encodings():
    f = one(Num("X", "S9(3)V99"))
    move(Decimal("-12.34"), f)
    assert f.raw == b"0123t"
    p = one(Num("X", "S9(3)V99", usage=COMP3))
    move(Decimal("-12.34"), p)
    assert p.raw == bytes.fromhex("01234D")
    u = one(Num("X", "9(3)", usage=COMP3))
    move(12, u)
    assert u.raw == bytes.fromhex("012F")


def test_division_intermediate_truncates():
    st = Storage("W", [Num("Q", "9V99"), Num("A", "9", value=1), Num("B", "9", value=3)])
    compute(st["Q"], dec(st["A"]) / dec(st["B"]) * dec(st["B"]))
    assert st["Q"].value == Decimal("0.99")
    compute(st["Q"], dec(st["A"]) / dec(st["B"]) * dec(st["B"]), rounded=True)
    assert st["Q"].value == Decimal("1.00")


def test_rounding_ties_away_from_zero():
    st = Storage("W", [Num("T", "S9V9"), Num("A", "S9V99")])
    for src, exp in (("1.25", "1.3"), ("-1.25", "-1.3"), ("1.24", "1.2"), ("-1.15", "-1.2")):
        move(Decimal(src), st["A"])
        compute(st["T"], dec(st["A"]), rounded=True)
        assert st["T"].value == Decimal(exp)


def test_size_error_leaves_target_unchanged():
    st = Storage("W", [Num("T", "S9(3)", value=5), Num("A", "S9(4)", value=999)])
    assert add(st["A"], st["T"], on_size_error=True) is True
    assert st["T"].value == 5
    assert add(st["A"], st["T"]) is True  # no phrase: truncated
    assert st["T"].value == 4


def test_negative_zero_after_truncation():
    st = Storage("W", [Group("G", [Num("A", "S9(4)")]), Num("S", "S9(6)", value=-10000)])
    move(st["S"], st["A"])
    assert st["A"].raw == b"000p"
    assert display_line(st["A"]) == b"+0000\n"


def test_comp5_wraps_and_comp_truncates():
    b5 = one(Num("X", "S9(4)", usage=COMP5))
    st = Storage("W", [Num("S", "S9(6)", value=99999)])
    move(st["S"], b5)
    assert display_line(b5) == b"-31073\n"
    b = one(Num("X", "S9(4)", usage=COMP))
    move(st["S"], b)
    assert display_line(b) == b"+9999\n"


def test_divide_remainder():
    st = Storage("W", [Num("A", "S9(3)", value=17), Num("B", "S9(3)", value=5),
                       Num("Q", "S9(3)"), Num("R", "S9(3)")])
    divide_remainder(st["A"], st["B"], st["Q"], st["R"])
    assert (st["Q"].value, st["R"].value) == (3, 2)


@pytest.mark.parametrize("pic,value,expected", [
    ("ZZZ.ZZ", "0", b"      "),
    ("***.**", "0", b"***.**"),
    ("ZZZ.ZZ", "0.05", b"   .05"),
    ("$$$,$$9.99CR", "-1234.5", b" $1,234.50CR"),
    ("---9", "1000", b" 000"),
    ("+ZZZ9", "5", b"+   5"),
    ("$ZZ,ZZ9.99DB", "-1", b"$     1.00DB"),
    ("+++9.99", "-1234.5", b"-234.50"),
])
def test_edit(pic, value, expected):
    st = Storage("W", [Num("S", "S9(7)V9(3)"), Edited("E", pic)])
    move(Decimal(value), st["S"])
    move(st["S"], st["E"])
    assert st["E"].raw == expected


def test_edit_unsupported_combination():
    # refused as soon as the item is initialised (its initial value is an edited zero)
    with pytest.raises(Unsupported):
        Storage("W", [Edited("E", "-$$$9.99")])


def test_alnum_moves_and_figuratives():
    st = Storage("W", [Alnum("X", "X(5)"), Num("N", "9(3)V9")])
    move("AB", st["X"])
    assert st["X"].raw == b"AB   "
    move("ABCDEFG", st["X"])
    assert st["X"].raw == b"ABCDE"
    move("12", st["N"])
    assert st["N"].raw == b"0120"
    with pytest.raises(MoveError):
        move("1 2", st["N"])
    move(SPACES, st["X"])
    assert st["X"].raw == b"     "
    move(ZEROS, st["N"])
    assert st["N"].value == 0


def test_redefines_and_occurs():
    st = Storage("W", [
        Group("D", [Num("YYYY", "9(4)"), Num("MM", "99"), Num("DD", "99")]),
        Num("DN", "9(8)", redefines="D"),
        Group("T", [Alnum("CODE", "X(2)"), Num("QTY", "9(3)")], occurs=3),
    ])
    move(20261013, st["DN"])
    assert (st["YYYY"].value, st["MM"].value, st["DD"].value) == (2026, 10, 13)
    move("AB", st.f("CODE", 2))
    move(7, st.f("QTY", 3))
    assert st.f("T", 1).size == 5 and st.size == 8 + 15
    assert st.f("CODE", 2).raw == b"AB"
    assert st.f("QTY", 3).raw == b"007"
    with pytest.raises(IndexError):
        st.f("CODE", 4)


def test_float_rejected():
    with pytest.raises(TypeError):
        CobDecimal.of(1.5)


def test_inspect_phrases_processed_one_after_another():
    from cobol_equiv.runtime import Phrase, inspect_replacing, inspect_tallying

    st = Storage("W", [Alnum("X", "X(6)", value="ABCABC"), Num("C1", "99"), Num("C2", "99")])
    inspect_tallying(st["X"], [Phrase("ALL", "BC", counter=st["C1"]),
                               Phrase("ALL", "AB", counter=st["C2"])])
    assert (st["C1"].value, st["C2"].value) == (2, 0)
    inspect_replacing(st["X"], [Phrase("ALL", "BC", by="xy"), Phrase("ALL", "AB", by="pq")])
    assert st["X"].raw == b"AxyAxy"


def test_trailing_sign_reads_next_sender_digit():
    st = Storage("W", [Num("S", "S9(5)V9(3)"), Edited("E", "ZZZ9-")])
    move(Decimal("-0.5"), st["S"])
    move(st["S"], st["E"])
    assert st["E"].raw == b"   0-"


def test_literal_truncated_to_zero_keeps_sign():
    f = one(Num("X", "S9V99"))
    move(Decimal("-0.004"), f)
    assert f.raw == b"00p"


def test_alnum_to_edited_refused():
    st = Storage("W", [Alnum("A", "X(3)", value="123"), Edited("E", "ZZZ9")])
    with pytest.raises(Unsupported):
        move(st["A"], st["E"])

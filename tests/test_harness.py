"""Harness unit tests that do not need GnuCOBOL."""

import pytest

from cobol_equiv.harness.cobol import CobolError, check_deterministic, check_fixed_format
from cobol_equiv.harness.compare import columns, compare, first_difference
from cobol_equiv.harness.corpus import apply_mutant
from cobol_equiv.harness.spec import STDOUT, OutputLayout, make_records
from cobol_equiv.runtime import Alnum, Num


def test_first_difference_names_the_field():
    layout = OutputLayout(lambda line: columns(("ID", 3), ("AMOUNT", 6)))
    d = first_difference(STDOUT, b"A01 12.50\nA02 99.99\n", b"A01 12.50\nA02 99.98\n", layout)
    assert (d.line, d.field, d.expected, d.actual) == (2, "AMOUNT", b" 99.99", b" 99.98")
    assert "field AMOUNT" in d.describe()


def test_first_difference_without_layout_and_missing_lines():
    d = first_difference(STDOUT, b"abc\n", b"abd\n")
    assert (d.line, d.column) == (1, 3)
    d = first_difference(STDOUT, b"a\nb\n", b"a\n")
    assert "missing" in d.detail
    assert first_difference(STDOUT, b"same", b"same") is None


def test_record_length_layout_and_missing_file():
    layout = OutputLayout(lambda rec: columns(("K", 2), ("V", 2)), record_length=4)
    d = first_difference("F.DAT", b"AA\x00\x01BB\x00\x02", b"AA\x00\x01BB\x00\x03", layout)
    assert (d.line, d.field) == (2, "V")
    d = compare(b"", {"F.DAT": b"x"}, b"", {}, ["F.DAT"], {})
    assert "missing" in d.detail


def test_nondeterministic_sources_rejected():
    with pytest.raises(CobolError):
        check_deterministic("           MOVE FUNCTION CURRENT-DATE TO X\n")
    with pytest.raises(CobolError):
        check_deterministic("           ACCEPT WS-D FROM DATE\n")
    check_deterministic("      * CURRENT-DATE in a comment is fine\n")
    with pytest.raises(CobolError):
        check_fixed_format("x" * 73 + "\n")


def test_apply_mutant_requires_unique_match():
    m = {"id": "m", "edits": [("a = 1", "a = 2")]}
    assert apply_mutant("a = 1\n", m) == "a = 2\n"
    with pytest.raises(ValueError):
        apply_mutant("a = 1\na = 1\n", m)


def test_make_records_uses_move_semantics():
    rec = make_records([Alnum("K", "X(3)"), Num("V", "S9(3)V99")], [{"K": "AB", "V": "-1.5"}])
    assert rec == b"AB 0015p\n"


def test_split_accept_from_date_rejected_and_access_random_allowed():
    with pytest.raises(CobolError):
        check_deterministic("           ACCEPT WS-D\n               FROM DATE\n")
    check_deterministic("               ACCESS MODE IS RANDOM\n")


def test_sys_exit_in_translation_is_a_difference(tmp_path):
    from cobol_equiv.harness.check import run_once
    from cobol_equiv.harness.spec import ProgramSpec

    exe = tmp_path / "prog"
    exe.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    exe.chmod(0o755)

    def main(stdin, files):
        raise SystemExit(0)

    d = run_once(ProgramSpec("p", "x", tmp_path / "p.cob"), exe, main, {})
    assert d is not None and "SystemExit" in d.detail

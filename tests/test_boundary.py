"""The boundary vectors depend on the record layouts only."""

import ast
from decimal import Decimal
from pathlib import Path

from cobol_equiv.harness import boundary
from cobol_equiv.harness.spec import InputSpec
from cobol_equiv.runtime import Alnum, Num, Storage


def test_numeric_boundaries_for_signed_two_decimals():
    item = next(i for i, _ in boundary.elementary_slots(Storage("R", [Num("A", "S9(2)V99")])))
    vals = boundary.numeric_boundaries(item)
    for v in ("0", "0.01", "99.99", "99.98", "10.00", "0.09", "0.10", "0.05", "0.50", "5.00",
              "-99.99", "-0.05"):
        assert Decimal(v) in vals, v
    assert boundary.NEG_ZERO in vals


def test_files_respect_max_records_and_include_an_empty_file():
    spec = InputSpec("F.DAT", [Alnum("K", "X(2)"), Num("N", "9(3)")], 0, 4)
    files = boundary.boundary_files(spec)
    assert files[0] == b""
    assert all(f.count(b"\n") <= 4 for f in files)


def test_generator_does_not_look_at_mutants_or_translations():
    tree = ast.parse(Path(boundary.__file__).read_text(encoding="utf-8"))
    imported = {n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    imported |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert not [m for m in imported if "corpus" in m or "mutant" in m or "check" in m]
    src = Path(boundary.__file__).read_text(encoding="utf-8")
    for word in ("mutant", "reference", "overrides", "vectors="):
        assert word not in src.split('"""', 2)[2], word

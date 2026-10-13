"""Corpus reference translations pass the harness; the harness detects a
deliberately wrong translation for every program."""

import csv
from pathlib import Path

import pytest

from cobol_equiv.cobc import version_label
from cobol_equiv.harness.check import check
from cobol_equiv.harness.corpus import (load_mutants, load_mutated, load_reference, load_spec,
                                        program_dirs)

DIRS = program_dirs()


def test_corpus_has_ten_programs():
    assert len(DIRS) == 10


ROOT = Path(__file__).resolve().parents[2]


def committed_corpus() -> dict:
    p = ROOT / "results" / f"gnucobol-{version_label()}" / "corpus.csv"
    if not p.exists():
        return {}
    with p.open(encoding="utf-8", newline="") as fh:
        return {r["program"]: r for r in csv.DictReader(fh)}


@pytest.mark.oracle
@pytest.mark.parametrize("d", DIRS, ids=lambda d: d.name)
def test_reference_translation_passes(d):
    """On GnuCOBOL 3.1.2 (the version the translations target) every reference
    translation must pass. On another version a program may fail; the test
    then requires the failure recorded in results/ for that version, found by
    a regression vector."""
    spec = load_spec(d)
    r = check(spec, load_reference(d).main, examples=25)
    if version_label() == "3.1.2":
        assert r.passed, r.difference.describe()
        return
    rec = committed_corpus().get(spec.name)
    assert rec is not None, "no committed corpus results for this compiler"
    if rec["result"] == "pass":
        assert r.passed, r.difference.describe()
    else:
        assert not r.passed
        if r.failing_source.startswith("vector"):
            # a fixed vector does not depend on the number of generated inputs
            assert rec["difference"] == f"{r.failing_source}: {r.difference.describe()}"
        else:
            assert rec["difference"].startswith(r.failing_source)


@pytest.mark.oracle
@pytest.mark.parametrize("d", DIRS, ids=lambda d: d.name)
def test_a_wrong_translation_is_detected(d):
    killed_by_vector = [m for m in load_mutants(d) if not m.get("equivalent")]
    spec = load_spec(d)
    results = [check(spec, load_mutated(d, m).main, examples=0) for m in killed_by_vector]
    assert any(not r.passed for r in results)

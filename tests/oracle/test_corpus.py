"""Corpus reference translations pass the harness; the harness detects a
deliberately wrong translation for every program."""

import pytest

from cobol_equiv.harness.check import check
from cobol_equiv.harness.corpus import (load_mutants, load_mutated, load_reference, load_spec,
                                        program_dirs)

DIRS = program_dirs()


def test_corpus_has_ten_programs():
    assert len(DIRS) == 10


@pytest.mark.oracle
@pytest.mark.parametrize("d", DIRS, ids=lambda d: d.name)
def test_reference_translation_passes(d):
    r = check(load_spec(d), load_reference(d).main, examples=25)
    assert r.passed, r.difference.describe()


@pytest.mark.oracle
@pytest.mark.parametrize("d", DIRS, ids=lambda d: d.name)
def test_a_wrong_translation_is_detected(d):
    killed_by_vector = [m for m in load_mutants(d) if not m.get("equivalent")]
    spec = load_spec(d)
    results = [check(spec, load_mutated(d, m).main, examples=0) for m in killed_by_vector]
    assert any(not r.passed for r in results)

"""Runtime vs GnuCOBOL over all generated oracle cases, for the compiler
under test (COBC, default cobc on PATH).

* GnuCOBOL 3.1.2 is the version the runtime models: any disagreement fails.
* Other versions: disagreements are expected where the compiler behaves
  differently; the test requires the results to be exactly the committed
  ones in results/gnucobol-<version>/, so a change shows up as a failure.
* For every version, an unsupported case must have a documented reason, and
  the committed CSV must be what a fresh run produces.
"""

import csv
from pathlib import Path

import pytest

from cobol_equiv.cobc import version_label
from cobol_equiv.oracle.run import run
from cobol_equiv.report import UNSUPPORTED_CATEGORIES, unsupported_category

ROOT = Path(__file__).resolve().parents[2]
DOCUMENTED = {k for k, _, _ in UNSUPPORTED_CATEGORIES}


def committed_path() -> Path:
    return ROOT / "results" / f"gnucobol-{version_label()}" / "oracle_cases.csv"


@pytest.fixture(scope="module")
def rows():
    return run(build=ROOT / ".cobol-build" / "oracle")


@pytest.mark.oracle
def test_no_disagreement_with_modelled_version(rows):
    if version_label() != "3.1.2":
        pytest.skip("the runtime models GnuCOBOL 3.1.2; other versions are compared with "
                    "their committed results instead")
    bad = [r for r in rows if r["outcome"] in ("disagree", "gnucobol-crash")]
    assert not bad, "\n".join(f"{r['rule']}: {r['params']}\n  G {r['gnucobol']}\n  P {r['python']}"
                              for r in bad[:10])


@pytest.mark.oracle
def test_unsupported_only_documented(rows):
    for r in rows:
        if r["outcome"] == "unsupported":
            msg = r["python"].split("UNSUPPORTED ", 1)[1]
            assert unsupported_category(msg) in DOCUMENTED, msg


@pytest.mark.oracle
def test_committed_results_are_reproducible(rows):
    path = committed_path()
    assert path.exists(), f"no committed results for GnuCOBOL {version_label()}: run cobol_equiv.reproduce"
    with path.open(encoding="utf-8", newline="") as fh:
        committed = list(csv.DictReader(fh))
    fresh = [{k: str(v) for k, v in r.items()} for r in rows]
    assert len(committed) == len(fresh)
    diff = [(a, b) for a, b in zip(committed, fresh) if a != b]
    assert not diff, f"{len(diff)} rows differ, first: {diff[0]}"

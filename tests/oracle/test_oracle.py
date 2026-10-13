"""Runtime vs GnuCOBOL over all generated oracle cases.

Fails on any disagreement, on an unsupported case outside the documented
reasons, and when results/oracle_cases.csv is not what a fresh run produces
(so the committed numbers stay reproducible).
"""

import csv
from pathlib import Path

import pytest

from cobol_equiv.oracle.run import run

ROOT = Path(__file__).resolve().parents[2]
ALLOWED_UNSUPPORTED = (
    "store of a value >= 2**63 into binary item",
    "PICTURE -$$$9.99: a fixed leading sign or currency symbol combined with a floating string",
)


@pytest.fixture(scope="module")
def rows():
    return run(build=ROOT / ".cobol-build" / "oracle")


@pytest.mark.oracle
def test_no_disagreement(rows):
    bad = [r for r in rows if r["outcome"] == "disagree"]
    assert not bad, "\n".join(f"{r['rule']}: {r['params']}\n  G {r['gnucobol']}\n  P {r['python']}"
                              for r in bad[:10])


@pytest.mark.oracle
def test_unsupported_only_documented(rows):
    for r in rows:
        if r["outcome"] == "unsupported":
            msg = r["python"].split("UNSUPPORTED ", 1)[1]
            assert msg.startswith(ALLOWED_UNSUPPORTED), msg


@pytest.mark.oracle
def test_committed_results_are_reproducible(rows):
    with (ROOT / "results" / "oracle_cases.csv").open(encoding="utf-8", newline="") as fh:
        committed = list(csv.DictReader(fh))
    fresh = [{k: str(v) for k, v in r.items()} for r in rows]
    assert len(committed) == len(fresh)
    diff = [(a, b) for a, b in zip(committed, fresh) if a != b]
    assert not diff, f"{len(diff)} rows differ, first: {diff[0]}"

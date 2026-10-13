"""Regenerate everything in results/ from scratch.

    python -m cobol_equiv.reproduce [--out results]

Runs the oracle (runtime vs GnuCOBOL), the corpus (reference translations vs
GnuCOBOL), the mutation run, and writes environment.csv and SUMMARY.md.
Requires cobc on PATH and the dev extras (hypothesis). Generated inputs are
deterministic for a given Hypothesis version; requirements-repro.txt pins the
versions used for the committed results.
"""

from __future__ import annotations

import argparse
import csv
import platform
import sys
from pathlib import Path

from .cobc import COBC_FLAGS, cobc_version


def write_environment(out: Path, examples: int) -> None:
    import hypothesis

    from .oracle.rules import SEED

    rows = [
        ("cobc", cobc_version()),
        ("cobc flags", " ".join(COBC_FLAGS)),
        ("platform", f"{platform.system()} {platform.machine()}"),
        ("oracle seed", str(SEED)),
        ("hypothesis", hypothesis.__version__),
        ("generated inputs per program and mutant (max)", str(examples)),
    ]
    with (out / "environment.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["key", "value"])
        w.writerows(rows)


def main(argv=None) -> int:
    from .harness import corpus_run, mutation_run
    from .oracle import run as oracle_run
    from . import report

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results")
    ap.add_argument("--examples", type=int, default=corpus_run.DEFAULT_EXAMPLES)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rc = 0
    rc |= oracle_run.main(["--out", str(out)])
    rc |= corpus_run.main(["--out", str(out), "--examples", str(a.examples)])
    rc |= mutation_run.main(["--out", str(out), "--examples", str(a.examples)])
    write_environment(out, a.examples)
    report.main(["--results", str(out)])
    print(f"results written to {out}/")
    return rc


if __name__ == "__main__":
    sys.exit(main())

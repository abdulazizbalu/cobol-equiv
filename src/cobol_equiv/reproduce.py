"""Regenerate the results for the selected compiler from scratch.

    python -m cobol_equiv.reproduce [--results results]
    COBC=/opt/gnucobol-3.2/bin/cobc python -m cobol_equiv.reproduce

Runs the oracle (runtime vs GnuCOBOL), the corpus (reference translations vs
GnuCOBOL) and the mutation run with the compiler named by COBC (default:
cobc on PATH), writes results/gnucobol-<version>/, then regenerates the
cross-version files, SUMMARY.md and the README results block from whatever
version directories exist.
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

from .cobc import COBC_FLAGS, cobc_version, results_dir, version_label


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
    ap.add_argument("--results", default="results")
    ap.add_argument("--examples", type=int, default=corpus_run.DEFAULT_EXAMPLES)
    a = ap.parse_args(argv)
    out = results_dir(a.results)
    out.mkdir(parents=True, exist_ok=True)
    # Exit codes of the steps are not used here: disagreements with a
    # compiler other than 3.1.2 are expected and are part of the results.
    # The test suite decides what is acceptable.
    oracle_run.main(["--out", str(out)])
    corpus_run.main(["--out", str(out), "--examples", str(a.examples)])
    # Mutation testing measures the harness against the compiler the reference
    # translations target; on other versions some references already fail.
    if version_label() == "3.1.2":
        mutation_run.main(["--out", str(out), "--examples", str(a.examples)])
    write_environment(out, a.examples)
    report.main(["--results", str(a.results)])
    print(f"results written to {out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())

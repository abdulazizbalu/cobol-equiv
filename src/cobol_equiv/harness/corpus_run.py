"""Run every corpus reference translation against GnuCOBOL.

    python -m cobol_equiv.harness.corpus_run [--examples 200] [--out results]
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from ..cobc import results_dir
from .check import check, check_boundary, import_hits
from .corpus import load_reference, load_spec, program_dirs

DEFAULT_EXAMPLES = 200


def run(examples: int = DEFAULT_EXAMPLES) -> list[dict]:
    rows = []
    for d in program_dirs():
        spec = load_spec(d)
        ref = load_reference(d)
        main, hits = ref.main, import_hits(ref)
        r = check(spec, main, examples, hits_at_import=hits)
        nb, bad, bd = check_boundary(spec, main, hits_at_import=hits)
        rows.append({
            "program": spec.name, "area": spec.area, "vectors": f"{r.vectors_passed}/{r.vectors}",
            "generated": r.generated,
            "result": {"pass": "pass", "fail": "FAIL", "unsupported": "UNSUPPORTED"}[r.status],
            "difference": "" if r.passed else f"{r.failing_source}: {r.difference.describe()}",
            "boundary vectors": nb,
            "boundary result": "pass" if bad is None else ("UNSUPPORTED" if bd.unsupported else "FAIL"),
            "boundary difference": "" if bad is None else f"boundary {bad}: {bd.describe()[:300]}",
        })
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--examples", type=int, default=DEFAULT_EXAMPLES)
    ap.add_argument("--out", default=None, help="default: results/gnucobol-<version>")
    a = ap.parse_args(argv)
    rows = run(a.examples)
    out = Path(a.out) if a.out else results_dir()
    out.mkdir(parents=True, exist_ok=True)
    with (out / "corpus.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(f"{r['program']:10} {r['result']} vectors {r['vectors']} generated {r['generated']} {r['difference']}")
    return 0 if all(r["result"] == r["boundary result"] == "pass" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())

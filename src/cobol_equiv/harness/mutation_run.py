"""Mutation testing of the harness: run deliberately wrong translations.

    python -m cobol_equiv.harness.mutation_run [--examples 200] [--out results]

Each corpus program has mutants.py with MUTANTS = [{id, category,
description, edits: [(find, replace), ...], equivalent, note}]. A mutant
is "killed" when the harness reports a difference against GnuCOBOL (on a
regression vector or a generated input, including a crash of the mutated
translation), "survived" otherwise.

`equivalent: True` marks a mutant that, by manual analysis written in
`note`, cannot change the output on the program's input domain. This is a
judgement, not a proof; the report shows it separately from survivors that
the harness simply missed.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from ..cobc import results_dir
from .check import check
from .corpus import load_mutants, load_mutated, load_spec, program_dirs

DEFAULT_EXAMPLES = 200
CATEGORIES = ("float", "rounding", "truncation", "sign", "off-by-one", "branch")


def run(examples: int = DEFAULT_EXAMPLES, programs: list[str] | None = None) -> list[dict]:
    rows = []
    for d in program_dirs():
        if programs and d.name not in programs:
            continue
        spec = load_spec(d)
        for m in load_mutants(d):
            if m["category"] not in CATEGORIES:
                raise ValueError(f"{d.name}/{m['id']}: unknown category {m['category']}")
            r = check(spec, load_mutated(d, m).main, examples)
            killed = not r.passed
            rows.append({
                "program": spec.name, "mutant": m["id"], "category": m["category"],
                "description": m["description"],
                "status": "killed" if killed else "survived",
                "survivor_kind": "" if killed else ("equivalent" if m.get("equivalent") else "missed"),
                "detected_by": r.failing_source if killed else "",
                "difference": r.difference.describe()[:300] if killed else "",
                "note": "" if killed else m.get("note", ""),
            })
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--examples", type=int, default=DEFAULT_EXAMPLES)
    ap.add_argument("--out", default=None, help="default: results/gnucobol-<version>")
    ap.add_argument("--programs", default="")
    a = ap.parse_args(argv)
    rows = run(a.examples, [p for p in a.programs.split(",") if p] or None)
    out = Path(a.out) if a.out else results_dir()
    out.mkdir(parents=True, exist_ok=True)
    if not a.programs:
        with (out / "mutation.csv").open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    for r in rows:
        print(f"{r['program']:10} {r['mutant']:28} {r['status']:8} {r['detected_by']:10} {r['difference'][:90]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

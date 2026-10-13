"""Mutation testing of the harness: run deliberately wrong translations.

    python -m cobol_equiv.harness.mutation_run [--examples 200] [--out results]

Each corpus program has mutants.py with MUTANTS = [{id, category,
description, edits: [(find, replace), ...], equivalent, note}]. A mutant
is "killed" when the harness reports a difference against GnuCOBOL (on a
regression vector or a generated input, including a crash of the mutated
translation), "survived" otherwise.

Two measurements per mutant: (a) the fixed regression vectors plus the
Hypothesis-generated inputs; (b) the same plus the general boundary vectors
of harness/boundary.py, which are derived from the PICTURE clauses only.

`equivalent: True` marks a mutant that, by the argument in docs/mutants.md
(checked by tests/test_equivalent_mutants.py where a bounded domain allows),
cannot change the output for any valid input. A mutant labelled equivalent
that either run kills is reported as "disproved".
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from ..cobc import results_dir
from .check import check, check_boundary, import_hits
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
            mod = load_mutated(d, m)
            main, hits = mod.main, import_hits(mod)
            r = check(spec, main, examples, hits_at_import=hits)
            killed = not r.passed
            if killed:
                killed_b, by_b, diff_b = True, r.failing_source, r.difference
            else:
                _, bad, bd = check_boundary(spec, main, hits_at_import=hits)
                killed_b, by_b, diff_b = bad is not None, (f"boundary {bad}" if bad else ""), bd
            equivalent = bool(m.get("equivalent"))
            rows.append({
                "program": spec.name, "mutant": m["id"], "category": m["category"],
                "description": m["description"],
                "status": "killed" if killed else "survived",
                "survivor_kind": "" if killed else ("equivalent" if equivalent else "missed"),
                "detected_by": r.failing_source if killed else "",
                "difference": r.difference.describe()[:300] if killed else "",
                "status_with_boundary": "killed" if killed_b else "survived",
                "detected_by_with_boundary": by_b,
                "difference_with_boundary": diff_b.describe()[:300] if killed_b else "",
                # a mutant labelled equivalent must survive both runs
                "equivalence": ("disproved" if equivalent and killed_b else
                                "claimed" if equivalent else ""),
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

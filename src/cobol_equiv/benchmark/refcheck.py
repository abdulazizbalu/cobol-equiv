"""Check criterion E4 for the benchmark corpus: the reference translation of
every program passes all of its materialised vectors (VISIBLE, DEV and
HELD-OUT) against GnuCOBOL 3.1.2, run the same way as translations.

    python -m cobol_equiv.benchmark.refcheck [--programs a,b]

Each reference runs with both CobDecimal comparison behaviours (deviation
D14: "registered", runtime 1.0.0, and "corrected", runtime 1.1.0) and must
pass with both; the CobDecimal comparison and hash calls it makes are
printed ("cmp").
"""

from __future__ import annotations

import argparse
import sys

from .programs import all_programs
from .runner import judge, run_translation
from .vectors import PRIMARY, decode_input, load, vectors_path


def check_program(p, runtime: str | None = None) -> tuple[int, int, list[str], dict]:
    spec = p.spec()
    if not vectors_path(p).exists():
        return 0, 0, ["no materialised vectors"], {}
    doc = load(p)
    items = [(s, v) for s, vs in doc["sets"].items() for v in vs]
    results = run_translation(p.dir / "reference.py", [decode_input(v["input"]) for _, v in items],
                              spec.timeout, "A", runtime=runtime)
    cmp = {k: sum(r.get("cmp", {}).get(k, 0) for r in results) for k in ("eq", "eq_diff", "order", "hash")}
    bad = []
    for (s, v), r in zip(items, results):
        verdict = judge(spec, v["expected"][PRIMARY], r)
        if not verdict.passed:
            bad.append(f"{s} {v['source']}: {verdict.kind}: {verdict.detail[:300]}")
    held = len(doc["sets"]["heldout"])
    lost = sum(1 for r in doc["removed"] if r["set"] == "heldout")
    return len(items), held, bad + ([f"{lost} of {held + lost} HELD-OUT inputs removed (over 10%)"]
                                    if lost * 10 > held + lost else []), cmp


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--programs", default="")
    a = ap.parse_args(argv)
    names = [n for n in a.programs.split(",") if n]
    failed = 0
    for p in all_programs():
        if names and p.name not in names:
            continue
        for runtime in ("registered", "corrected"):
            n, held, bad, cmp = check_program(p, runtime)
            print(f"{p.track} {p.name:40} {runtime:10} vectors {n} heldout {held} "
                  f"{'FAIL' if bad else 'pass'} cmp {cmp}")
            for b in bad[:5]:
                print("    " + b)
            failed += bool(bad)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

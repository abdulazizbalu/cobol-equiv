"""Verify the committed translations (docs/benchmark-protocol.md, section 4).

    python -m cobol_equiv.benchmark.verify [--check]

Runs every committed translation under benchmark/runs/{E,R}/ on the
committed vectors and writes benchmark/results/verdicts.csv, one row per
(program, condition, attempt, round, set, compiler version):

- conditions A and C: round 0 is the translation of the call;
- condition B: round k (0-3) is the version current after k repair rounds
  (round 0 is the A translation); after the attempt stopped, the last
  version carries over to the later rounds. Round 3 is the final version.

Sets are VISIBLE, DEV and HELD-OUT on GnuCOBOL 3.1.2; HELD-OUT on 3.2 is
added for translations that pass HELD-OUT on 3.1.2 (the secondary re-run).
With --check the file is regenerated in memory and compared with the
committed one. Generation of translations is not reproducible; this
verification is.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

from .programs import Program, programs
from .runner import judge, run_translation
from .vectors import PRIMARY, decode_input, load

ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "benchmark" / "runs"
OUT = ROOT / "benchmark" / "results" / "verdicts.csv"
SECONDARY = "3.2"
ROUNDS = 3
FIELDS = ["track", "program", "condition", "attempt", "round", "version", "set", "vectors", "passed",
          "pass", "first_failure_kind", "first_failure", "translation"]


def versions(p: Program, condition: str, attempt: int) -> list[Path | None] | None:
    """The translation file of each round (None: no code), or None if the
    attempt has not been run."""
    base = RUNS / p.track / p.name
    if condition in ("A", "C"):
        d = base / condition / str(attempt)
        if not (d / "call.json").exists():
            return None
        f = d / "translation.py"
        return [f if f.exists() else None]
    b = base / "B" / str(attempt)
    final = b / "final.json"
    if not final.exists():
        return None
    a = base / "A" / str(attempt) / "translation.py"
    current = a if a.exists() else None
    out = [current]
    for k in range(1, ROUNDS + 1):
        d = b / f"round-{k}"
        if (d / "call.json").exists() and (d / "translation.py").exists():
            current = d / "translation.py"
        out.append(current)
    return out


def _evaluate(p: Program, path: Path | None, condition: str, items: list, label: str) -> dict:
    spec = p.spec()
    if path is None:
        return {"vectors": len(items), "passed": 0, "pass": 0, "first_failure_kind": "no code",
                "first_failure": ""}
    results = run_translation(path, [decode_input(v["input"]) for v in items], spec.timeout,
                              "C" if condition == "C" else "A")
    passed, first = 0, None
    for v, r in zip(items, results):
        verdict = judge(spec, v["expected"][label], r)
        if verdict.passed:
            passed += 1
        elif first is None:
            first = verdict
    return {"vectors": len(items), "passed": passed, "pass": int(first is None and bool(items)),
            "first_failure_kind": "" if first is None else first.kind,
            "first_failure": "" if first is None else first.detail[:300].replace("\n", " ")}


def rows_for(p: Program) -> list[dict]:
    doc = load(p)
    rows = []
    for condition in ("A", "B", "C"):
        for attempt in (1, 2, 3):
            vs = versions(p, condition, attempt)
            if vs is None:
                continue
            cache: dict = {}
            for rnd, path in enumerate(vs):
                for set_name in ("visible", "dev", "heldout"):
                    key = (path, set_name, PRIMARY)
                    if key not in cache:
                        cache[key] = _evaluate(p, path, condition, doc["sets"][set_name], PRIMARY)
                    res = cache[key]
                    rows.append(_row(p, condition, attempt, rnd, PRIMARY, set_name, res, path))
                    if set_name == "heldout" and res["pass"] and rnd == len(vs) - 1:
                        held = doc["sets"]["heldout"]
                        if any("error" in v["expected"][SECONDARY] for v in held):
                            continue  # no 3.2 expected outputs (protocol, D10)
                        key2 = (path, set_name, SECONDARY)
                        if key2 not in cache:
                            cache[key2] = _evaluate(p, path, condition, held, SECONDARY)
                        rows.append(_row(p, condition, attempt, rnd, SECONDARY, set_name, cache[key2], path))
    return rows


def _row(p, condition, attempt, rnd, label, set_name, res, path) -> dict:
    return {"track": p.track, "program": p.name, "condition": condition, "attempt": attempt,
            "round": rnd, "version": label, "set": set_name, **res,
            "translation": "" if path is None else path.relative_to(ROOT).as_posix()}


def generate() -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    for track in ("E", "R"):
        for p in programs(track):
            for row in rows_for(p):
                w.writerow(row)
    return buf.getvalue()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    text = generate()
    if a.check:
        committed = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if committed != text:
            print(f"{OUT} differs from a fresh verification run")
            return 1
        print("verdicts reproduced")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(json.dumps({"rows": text.count("\n") - 1}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Verify the committed translations (docs/benchmark-protocol.md, section 4).

    python -m cobol_equiv.benchmark.verify [--check] [--jobs N] [--fresh]

Runs every committed translation under benchmark/runs/{E,R}/ on the
committed vectors and writes benchmark/results/verdicts.csv, one row per
(program, condition, attempt, round, set, compiler version):

- conditions A and C: round 0 is the translation of the call;
- condition B: round k (0-3) is the version current after k repair rounds
  (round 0 is the A translation); after the attempt stopped, the last
  version carries over to the later rounds. Round 3 is the final version.

Sets are VISIBLE, DEV and HELD-OUT on GnuCOBOL 3.1.2; HELD-OUT on 3.2 is
added for translations that pass HELD-OUT on 3.1.2 (the secondary re-run).
The work is split into units, one per (program, condition, attempt), run in
parallel (--jobs, default: number of CPUs). Each finished unit is written
to benchmark/results/.verify-parts/ (not committed) under a key made of the
translation files, the vectors file and this module's unit version, so an
interrupted run resumes with the units not yet done; --fresh deletes the
saved units and the evaluation cache. Cache keys include the code of this
module, the runner, the driver and the vectors module. verdicts.csv is assembled from the units in a fixed order.
With --check the file is assembled the same way and compared with the
committed one, ignoring the two counts that depend on the machine's speed
(vectors that needed the extended time limit, vectors still timed out). Generation of translations is not reproducible; this
verification is.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from .programs import Program, programs
from .runner import judge, run_extended
from .vectors import PRIMARY, decode_input, load

ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "benchmark" / "runs"
OUT = ROOT / "benchmark" / "results" / "verdicts.csv"
PARTS = ROOT / "benchmark" / "results" / ".verify-parts"
UNIT_VERSION = "3"  # change when the rows of a unit are computed differently
_CODE = ("verify.py", "runner.py", "_driver.py", "vectors.py")


def _code_hash() -> str:
    """The code that produces the verdicts; part of every cache key."""
    h = hashlib.sha256(UNIT_VERSION.encode("utf-8"))
    for name in _CODE:
        h.update((Path(__file__).with_name(name)).read_bytes())
    return h.hexdigest()
SECONDARY = "3.2"
ROUNDS = 3
FIELDS = ["track", "program", "condition", "attempt", "round", "version", "set", "vectors", "passed",
          "pass", "slow_vectors", "timeout_vectors", "first_failure_kind", "first_failure", "translation"]


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


def _results(path: Path, condition: str, items: list, timeout: float) -> list[dict]:
    """Outputs of the translation on the items, run with run_extended; cached
    under PARTS/evals by the translation's bytes and the inputs (an A
    translation is also round 0 of B)."""
    python = "C" if condition == "C" else "A"
    inputs = [v["input"] for v in items]
    h = hashlib.sha256(f"{_code_hash()}|{python}|{timeout}|".encode("utf-8"))
    h.update(path.read_bytes())
    h.update(json.dumps(inputs, sort_keys=True).encode("utf-8"))
    cache = PARTS / "evals" / f"{h.hexdigest()}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    results = run_extended(path, [decode_input(x) for x in inputs], timeout, python)
    cache.parent.mkdir(parents=True, exist_ok=True)
    tmp = cache.with_name(f"{cache.stem}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(results), encoding="utf-8")
    tmp.replace(cache)
    return results


def _evaluate(p: Program, path: Path | None, condition: str, items: list, label: str) -> dict:
    """Summary of one translation on one set. A vector that exceeds the
    protocol's time limits but gives the right output under the extended
    limits passes (counted in slow_vectors). A vector still timed out there
    is not a semantic failure: the set then fails with kind "timeout", but
    only when no vector fails for another reason (D12)."""
    spec = p.spec()
    if path is None:
        return {"vectors": len(items), "passed": 0, "pass": 0, "slow_vectors": 0, "timeout_vectors": 0,
                "first_failure_kind": "no code", "first_failure": ""}
    results = _results(path, condition, items, spec.timeout)
    passed = slow = timeouts = 0
    first = first_timeout = None
    for v, r in zip(items, results):
        verdict = judge(spec, v["expected"][label], r)
        if verdict.passed:
            passed += 1
            slow += bool(r.get("slow"))
        elif verdict.kind == "timeout":
            timeouts += 1
            first_timeout = first_timeout or verdict
        elif first is None:
            first = verdict
    failure = first or first_timeout
    return {"vectors": len(items), "passed": passed, "pass": int(failure is None and bool(items)),
            "slow_vectors": slow, "timeout_vectors": timeouts,
            "first_failure_kind": "" if failure is None else failure.kind,
            "first_failure": "" if failure is None else failure.detail[:300].replace("\n", " ")}


def units() -> list[tuple[str, str, str, int]]:
    """(track, program, condition, attempt) of every run attempt, in report order."""
    out = []
    for track in ("E", "R"):
        for p in programs(track):
            for condition in ("A", "B", "C"):
                for attempt in (1, 2, 3):
                    if versions(p, condition, attempt) is not None:
                        out.append((track, p.name, condition, attempt))
    return out


def _program(track: str, name: str) -> Program:
    return next(p for p in programs(track) if p.name == name)


def unit_key(unit) -> str:
    track, name, condition, attempt = unit
    p = _program(track, name)
    h = hashlib.sha256(f"{_code_hash()}|{track}|{name}|{condition}|{attempt}".encode("utf-8"))
    from .vectors import vectors_path
    h.update(vectors_path(p).read_bytes())
    for path in versions(p, condition, attempt):
        h.update(b"|none|" if path is None else path.read_bytes())
    return h.hexdigest()


def unit_rows(unit) -> list[dict]:
    track, name, condition, attempt = unit
    p = _program(track, name)
    doc = load(p)
    vs = versions(p, condition, attempt)
    rows, cache = [], {}
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


def _part_path(unit) -> Path:
    track, name, condition, attempt = unit
    return PARTS / track / name / f"{condition}-{attempt}.json"


def _run_unit(unit) -> tuple:
    key = unit_key(unit)
    rows = unit_rows(unit)
    part = _part_path(unit)
    part.parent.mkdir(parents=True, exist_ok=True)
    tmp = part.with_suffix(".tmp")
    tmp.write_text(json.dumps({"key": key, "rows": rows}, sort_keys=True), encoding="utf-8")
    tmp.replace(part)
    return unit, rows


def _saved(unit):
    part = _part_path(unit)
    if not part.exists():
        return None
    doc = json.loads(part.read_text(encoding="utf-8"))
    return doc["rows"] if doc.get("key") == unit_key(unit) else None


def _row(p, condition, attempt, rnd, label, set_name, res, path) -> dict:
    return {"track": p.track, "program": p.name, "condition": condition, "attempt": attempt,
            "round": rnd, "version": label, "set": set_name, **res,
            "translation": "" if path is None else path.relative_to(ROOT).as_posix()}


def generate(jobs: int | None = None, fresh: bool = False, progress=None) -> str:
    if fresh and PARTS.exists():
        import shutil
        shutil.rmtree(PARTS)  # saved units and the evaluation cache
    all_units = units()
    done = {u: r for u in all_units if (r := _saved(u)) is not None}
    todo = [u for u in all_units if u not in done]
    if progress:
        progress(f"{len(all_units)} units: {len(done)} saved, {len(todo)} to run")
    # B round 0 is the A translation: run the A and C units first, so that the
    # B units find the A evaluations in the cache instead of repeating them.
    phases = [[u for u in todo if u[2] != "B"], [u for u in todo if u[2] == "B"]]
    i = 0
    with ProcessPoolExecutor(max_workers=jobs or os.cpu_count() or 1) as ex:
        for phase in phases:
            for f in as_completed([ex.submit(_run_unit, u) for u in phase]):
                unit, rows = f.result()
                done[unit] = rows
                i += 1
                if progress:
                    progress(f"{i}/{len(todo)} {'/'.join(map(str, unit))}")
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    for u in all_units:
        w.writerows(done[u])
    return buf.getvalue()


# How many vectors needed the extended time limit, or were still timed out,
# depends on the speed of the machine; the verdicts do not.
MACHINE_DEPENDENT = ("slow_vectors", "timeout_vectors")


def compare(committed: str, fresh: str) -> list[str]:
    def rows(text):
        return [{k: v for k, v in r.items() if k not in MACHINE_DEPENDENT}
                for r in csv.DictReader(io.StringIO(text))]

    a, b = rows(committed), rows(fresh)
    if len(a) != len(b):
        return [f"row count {len(a)} committed, {len(b)} fresh"]
    return [f"committed {x}\nfresh     {y}" for x, y in zip(a, b) if x != y]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--jobs", type=int, default=None)
    ap.add_argument("--fresh", action="store_true", help="delete saved units and the evaluation cache first")
    a = ap.parse_args(argv)
    text = generate(a.jobs, a.fresh, progress=lambda m: print(m, file=sys.stderr, flush=True))
    if a.check:
        committed = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        diffs = compare(committed, text)
        for d in diffs[:20]:
            print(d)
        if diffs:
            print(f"{OUT} differs from a fresh verification run ({len(diffs)} rows)")
            return 1
        print("verdicts reproduced")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(json.dumps({"rows": text.count("\n") - 1}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

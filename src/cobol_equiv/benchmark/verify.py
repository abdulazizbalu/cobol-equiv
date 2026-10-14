"""Verify the committed translations (docs/benchmark-protocol.md, section 4).

    python -m cobol_equiv.benchmark.verify [--runtime registered|corrected] [--check] [--jobs N] [--fresh]

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

--runtime selects the comparison behaviour of CobDecimal in conditions A
and B (deviation D14, see _driver.py). This command verifies the
"registered" mode (runtime 1.0.0, frozen for the benchmark) in full and
writes verdicts.csv, and comparisons.csv for the units of the D14 scope
(per translation and round, the CobDecimal comparison calls made on the
HELD-OUT vectors on GnuCOBOL 3.1.2; --check ignores these counts for rows
with timed-out vectors, where they depend on how far the run got). The
"corrected" mode (runtime 1.1.0) is verified within the D14 scope only, by
`python -m cobol_equiv.benchmark.ci sensitivity` (writes) and
`ci check --runtime corrected` (checks); this command refuses it.
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
RESULTS = ROOT / "benchmark" / "results"
MODES = ("registered", "corrected")
OUT = RESULTS / "verdicts.csv"
OUTS = {"registered": (OUT, RESULTS / "comparisons.csv"),
        "corrected": (RESULTS / "verdicts-corrected.csv", RESULTS / "comparisons-corrected.csv")}
PARTS = RESULTS / ".verify-parts"
UNIT_VERSION = "4"  # change when the rows of a unit are computed differently
_CODE = ("verify.py", "runner.py", "_driver.py", "vectors.py")
RUNTIME_DIR = Path(__file__).resolve().parents[1] / "runtime"


def _code_hash() -> str:
    """The code that produces the verdicts; part of every cache key."""
    h = hashlib.sha256(UNIT_VERSION.encode("utf-8"))
    for name in _CODE:
        h.update((Path(__file__).with_name(name)).read_bytes())
    return h.hexdigest()


def _runtime_hash() -> str:
    h = hashlib.sha256()
    for f in sorted(RUNTIME_DIR.glob("*.py")):
        h.update(f.name.encode("utf-8") + b"\0" + f.read_bytes())
    return h.hexdigest()


def _mode_key(condition: str, mode: str) -> str:
    """Condition C does not import the runtime: its evaluations are shared by the modes."""
    return "C" if condition == "C" else f"A|{mode}|{_runtime_hash()}"
SECONDARY = "3.2"
ROUNDS = 3
FIELDS = ["track", "program", "condition", "attempt", "round", "version", "set", "vectors", "passed",
          "pass", "slow_vectors", "timeout_vectors", "first_failure_kind", "first_failure", "translation"]
CMP = ("eq", "eq_diff", "order", "hash")
USAGE_FIELDS = ["track", "program", "condition", "attempt", "round", "timeout_vectors", *CMP, "translation"]


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


def _results(path: Path, condition: str, items: list, timeout: float, mode: str) -> list[dict]:
    """Outputs of the translation on the items, run with run_extended; cached
    under PARTS/evals by the translation's bytes and the inputs (an A
    translation is also round 0 of B)."""
    python = "C" if condition == "C" else "A"
    inputs = [v["input"] for v in items]
    h = hashlib.sha256(f"{_code_hash()}|{_mode_key(condition, mode)}|{timeout}|".encode("utf-8"))
    h.update(path.read_bytes())
    h.update(json.dumps(inputs, sort_keys=True).encode("utf-8"))
    cache = PARTS / "evals" / f"{h.hexdigest()}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    results = run_extended(path, [decode_input(x) for x in inputs], timeout, python, runtime=mode)
    cache.parent.mkdir(parents=True, exist_ok=True)
    tmp = cache.with_name(f"{cache.stem}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(results), encoding="utf-8")
    tmp.replace(cache)
    return results


def _evaluate(p: Program, path: Path | None, condition: str, items: list, label: str,
              mode: str) -> dict:
    """Summary of one translation on one set. A vector that exceeds the
    protocol's time limits but gives the right output under the extended
    limits passes (counted in slow_vectors). A vector still timed out there
    is not a semantic failure: the set then fails with kind "timeout", but
    only when no vector fails for another reason (D12)."""
    spec = p.spec()
    if path is None:
        return {"vectors": len(items), "passed": 0, "pass": 0, "slow_vectors": 0, "timeout_vectors": 0,
                "first_failure_kind": "no code", "first_failure": "", **dict.fromkeys(CMP, 0)}
    results = _results(path, condition, items, spec.timeout, mode)
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
            "first_failure": "" if failure is None else failure.detail[:300].replace("\n", " "),
            **{k: sum(r.get("cmp", {}).get(k, 0) for r in results) for k in CMP}}


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


def unit_key(unit, mode: str = "registered") -> str:
    track, name, condition, attempt = unit
    p = _program(track, name)
    h = hashlib.sha256(f"{_code_hash()}|{_mode_key(condition, mode)}|{track}|{name}|{condition}|{attempt}"
                       .encode("utf-8"))
    from .vectors import vectors_path
    h.update(vectors_path(p).read_bytes())
    h.update(b"|spec|" + (p.dir / "spec.py").read_bytes())  # outputs, layouts and time limit
    for path in versions(p, condition, attempt):
        h.update(b"|none|" if path is None else path.read_bytes())
    return h.hexdigest()


def unit_rows(unit, mode: str = "registered") -> list[dict]:
    track, name, condition, attempt = unit
    p = _program(track, name)
    doc = load(p)
    vs = versions(p, condition, attempt)
    rows, cache = [], {}
    for rnd, path in enumerate(vs):
        for set_name in ("visible", "dev", "heldout"):
            key = (path, set_name, PRIMARY)
            if key not in cache:
                cache[key] = _evaluate(p, path, condition, doc["sets"][set_name], PRIMARY, mode)
            res = cache[key]
            rows.append(_row(p, condition, attempt, rnd, PRIMARY, set_name, res, path))
            if set_name == "heldout" and res["pass"] and rnd == len(vs) - 1:
                held = doc["sets"]["heldout"]
                if any("error" in v["expected"][SECONDARY] for v in held):
                    continue  # no 3.2 expected outputs (protocol, D10)
                key2 = (path, set_name, SECONDARY)
                if key2 not in cache:
                    cache[key2] = _evaluate(p, path, condition, held, SECONDARY, mode)
                rows.append(_row(p, condition, attempt, rnd, SECONDARY, set_name, cache[key2], path))
    return rows


def _part_path(unit, mode: str) -> Path:
    track, name, condition, attempt = unit
    return PARTS / mode / track / name / f"{condition}-{attempt}.json"


def _run_unit(unit, mode: str) -> tuple:
    key = unit_key(unit, mode)
    rows = unit_rows(unit, mode)
    part = _part_path(unit, mode)
    part.parent.mkdir(parents=True, exist_ok=True)
    tmp = part.with_suffix(".tmp")
    tmp.write_text(json.dumps({"key": key, "rows": rows}, sort_keys=True), encoding="utf-8")
    tmp.replace(part)
    return unit, rows


def _saved(unit, mode: str):
    part = _part_path(unit, mode)
    if not part.exists():
        return None
    doc = json.loads(part.read_text(encoding="utf-8"))
    return doc["rows"] if doc.get("key") == unit_key(unit, mode) else None


def _row(p, condition, attempt, rnd, label, set_name, res, path) -> dict:
    return {"track": p.track, "program": p.name, "condition": condition, "attempt": attempt,
            "round": rnd, "version": label, "set": set_name, **res,
            "translation": "" if path is None else path.relative_to(ROOT).as_posix()}


def generate(jobs: int | None = None, fresh: bool = False, progress=None,
             mode: str = "registered") -> tuple[str, str]:
    """(verdicts CSV of every unit, comparisons CSV of the D14 scope units) of the mode."""
    from .ci import scope, workers

    affected, sampled = scope()
    in_scope = set(affected) | set(sampled)
    if fresh and PARTS.exists():
        import shutil
        shutil.rmtree(PARTS)  # saved units and the evaluation cache
    all_units = units()
    done = {u: r for u in all_units if (r := _saved(u, mode)) is not None}
    todo = [u for u in all_units if u not in done]
    if progress:
        progress(f"{len(all_units)} units: {len(done)} saved, {len(todo)} to run")
    # B round 0 is the A translation: run the A and C units first, so that the
    # B units find the A evaluations in the cache instead of repeating them.
    phases = [[u for u in todo if u[2] != "B"], [u for u in todo if u[2] == "B"]]
    i = 0
    with ProcessPoolExecutor(max_workers=jobs or workers()) as ex:
        for phase in phases:
            for f in as_completed([ex.submit(_run_unit, u, mode) for u in phase]):
                unit, rows = f.result()
                done[unit] = rows
                i += 1
                if progress:
                    progress(f"{i}/{len(todo)} {'/'.join(map(str, unit))}")
    buf, usage = io.StringIO(), io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n", extrasaction="ignore")
    wu = csv.DictWriter(usage, fieldnames=USAGE_FIELDS, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    wu.writeheader()
    for u in all_units:
        w.writerows(done[u])
        if u in in_scope:
            wu.writerows(r for r in done[u] if r["set"] == "heldout" and r["version"] == PRIMARY)
    return buf.getvalue(), usage.getvalue()


# How many vectors needed the extended time limit, or were still timed out,
# depends on the speed of the machine; the verdicts do not.
MACHINE_DEPENDENT = ("slow_vectors", "timeout_vectors")


def compare(committed: str, fresh: str) -> list[str]:
    """Differences between two verdicts or comparisons CSVs, ignoring the
    machine-dependent counts (and the comparison counts of rows with
    timed-out vectors)."""
    def rows(text):
        out = []
        for r in csv.DictReader(io.StringIO(text)):
            drop = set(MACHINE_DEPENDENT)
            if r.get("timeout_vectors", "0") != "0" and "eq" in r:
                drop |= set(CMP)
            out.append({k: v for k, v in r.items() if k not in drop})
        return out

    a, b = rows(committed), rows(fresh)
    if len(a) == len(b):
        # a row whose counts are dropped on one side only (a time-out on one machine)
        for x, y in zip(a, b):
            if set(x) != set(y):
                for k in CMP:
                    x.pop(k, None)
                    y.pop(k, None)
    if len(a) != len(b):
        return [f"row count {len(a)} committed, {len(b)} fresh"]
    return [f"committed {x}\nfresh     {y}" for x, y in zip(a, b) if x != y]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--jobs", type=int, default=None)
    ap.add_argument("--fresh", action="store_true", help="delete saved units and the evaluation cache first")
    ap.add_argument("--runtime", choices=MODES, default="registered")
    a = ap.parse_args(argv)
    if a.runtime == "corrected":
        print("the corrected mode is verified within the D14 scope: use "
              "python -m cobol_equiv.benchmark.ci sensitivity (write) or ci check --runtime corrected")
        return 2
    texts = generate(a.jobs, a.fresh, progress=lambda m: print(m, file=sys.stderr, flush=True),
                     mode=a.runtime)
    if a.check:
        bad = 0
        for out, text in zip(OUTS[a.runtime], texts):
            committed = out.read_text(encoding="utf-8") if out.exists() else ""
            diffs = compare(committed, text)
            for d in diffs[:20]:
                print(d)
            if diffs:
                print(f"{out} differs from a fresh verification run ({len(diffs)} rows)")
                bad += 1
        if bad:
            return 1
        print("verdicts reproduced")
        return 0
    for out, text in zip(OUTS[a.runtime], texts):
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(json.dumps({"rows": texts[0].count("\n") - 1}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

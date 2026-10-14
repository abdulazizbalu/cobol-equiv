"""Partial and split re-verification for CI (docs/benchmark.md, "Verification in CI").

    python -m cobol_equiv.benchmark.ci inputs [--check [--base REF]]
    python -m cobol_equiv.benchmark.ci check --runtime MODE [--track T] [--base REF --sample K] [--jobs N]

A full verification of one runtime mode takes hours, so CI does not run
both modes on every pull request:

- `inputs` writes benchmark/results/verify-inputs.json: for each runtime mode
  and unit (track, program, condition, attempt), the SHA-256 of what decides
  its verdicts: the translation files of the unit, the vectors file, the
  program's spec, the verification code (verify, runner, driver, vectors),
  the runtime mode and, for conditions A and B, the runtime version. It also
  records the SHA-256 of the runtime's source: --check fails when the file
  is not current, and with --base REF also when the runtime's source
  differs from that on REF under the same version number.
- `check --base REF --sample K` (pull requests) verifies the units whose
  input hash or committed rows differ from those on the git ref REF (the
  base branch), plus a fixed sample: K units per (track, condition),
  drawn with the seed crc32("ci-sample") from the remaining units. Their
  rows are compared with the committed verdicts and comparisons files.
- `check` without --base (the scheduled and manually started workflow)
  verifies every unit of the mode, or of one track with --track.

Units are run with verify's own functions; finished units are saved under
benchmark/results/.verify-parts/ with verify's keys (which include the
content of the translation files, the vectors, the runtime and the
verification code), which CI keeps between runs with actions/cache. The
sample units are always run again, with an empty cache.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import random
import subprocess
import sys
import zlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from . import verify
from .vectors import vectors_path

INPUTS = verify.RESULTS / "verify-inputs.json"
SEED = zlib.crc32(b"ci-sample")


def workers() -> int:
    """CPU cores minus one, at least one."""
    return max(1, (os.cpu_count() or 2) - 1)


def runtime_version() -> str:
    from .. import runtime

    return runtime.__version__


def input_hash(unit, mode: str) -> str:
    track, name, condition, attempt = unit
    p = verify._program(track, name)
    runtime = "none" if condition == "C" else f"{mode}|{runtime_version()}"
    h = hashlib.sha256(f"{track}|{name}|{condition}|{attempt}|{runtime}|{verify._code_hash()}".encode("utf-8"))
    h.update(vectors_path(p).read_bytes())
    h.update((p.dir / "spec.py").read_bytes())
    for path in verify.versions(p, condition, attempt):
        h.update(b"|none|" if path is None else b"|" + path.read_bytes())
    return h.hexdigest()


def unit_id(unit) -> str:
    return "/".join(map(str, unit))


def inputs_doc() -> dict:
    us = verify.units()
    return {"runtime_version": runtime_version(), "runtime_sha256": verify._runtime_hash(),
            "units": {m: {unit_id(u): input_hash(u, m) for u in us} for m in verify.MODES}}


def _git_show(ref: str, path) -> str | None:
    rel = path.relative_to(verify.ROOT).as_posix()
    r = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=verify.ROOT, capture_output=True)
    return r.stdout.decode("utf-8") if r.returncode == 0 else None


def _rows_by_unit(text: str | None) -> dict:
    out: dict = {}
    for r in csv.DictReader(io.StringIO(text or "")):
        out.setdefault("/".join(r[k] for k in ("track", "program", "condition", "attempt")), []).append(r)
    return out


def changed_units(mode: str, base: str) -> list:
    """Units whose input hash, or committed verdict or comparison rows, differ
    from those on the git ref base. When base has no verify-inputs.json (it
    predates this record), only the rows are compared."""
    old_inputs = _git_show(base, INPUTS)
    old = json.loads(old_inputs)["units"].get(mode, {}) if old_inputs else None
    out_v, out_c = verify.OUTS[mode]
    rows_old = [_rows_by_unit(_git_show(base, out_v)), _rows_by_unit(_git_show(base, out_c))]
    rows_new = [_rows_by_unit(f.read_text(encoding="utf-8") if f.exists() else "") for f in (out_v, out_c)]
    changed = []
    for u in verify.units():
        i = unit_id(u)
        if (old is not None and old.get(i) != input_hash(u, mode)) or any(a.get(i) != b.get(i) for a, b in zip(rows_old, rows_new)):
            changed.append(u)
    return changed


def sample(units: list, k: int) -> list:
    """k units per (track, condition), fixed seed, from the given units."""
    rnd = random.Random(SEED)
    out = []
    for track in ("E", "R"):
        for cond in ("A", "B", "C"):
            stratum = [u for u in units if u[0] == track and u[2] == cond]
            out += rnd.sample(stratum, min(k, len(stratum)))
    return out


def _set_parts(path: str) -> None:
    verify.PARTS = Path(path)  # in each worker, whatever the start method


def run_units(units: list, mode: str, jobs: int | None, progress) -> dict:
    done = {u: r for u in units if (r := verify._saved(u, mode)) is not None}
    todo = [u for u in units if u not in done]
    progress(f"{len(units)} units ({mode}): {len(done)} saved, {len(todo)} to run")
    phases = [[u for u in todo if u[2] != "B"], [u for u in todo if u[2] == "B"]]
    i = 0
    with ProcessPoolExecutor(max_workers=jobs or workers(), initializer=_set_parts,
                             initargs=(str(verify.PARTS),)) as ex:
        for phase in phases:
            for f in as_completed([ex.submit(verify._run_unit, u, mode) for u in phase]):
                unit, rows = f.result()
                done[unit] = rows
                i += 1
                progress(f"{i}/{len(todo)} {unit_id(unit)}")
    return done


def check(mode: str, track: str | None, base: str | None, k: int, jobs: int | None, progress) -> int:
    missing = [f for f in (*verify.OUTS[mode], INPUTS) if not f.exists()]
    if missing:  # nothing to compare with: fail before hours of runs
        print("missing: " + ", ".join(f.relative_to(verify.ROOT).as_posix() for f in missing))
        return 1
    us = [u for u in verify.units() if track is None or u[0] == track]
    bad = 0
    affected, sampled = scope()
    if mode == "corrected":
        # outside the D14 scope the corrected rows are the registered rows
        # (D14): check the copy instead of running the unit
        reg = _rows_by_unit(verify.OUT.read_text(encoding="utf-8"))
        cor = _rows_by_unit(verify.OUTS["corrected"][0].read_text(encoding="utf-8"))
        outside = [u for u in us if u not in affected and u not in sampled]
        for u in outside:
            if reg.get(unit_id(u)) != cor.get(unit_id(u)):
                print(f"verdicts-corrected.csv {unit_id(u)}: outside the D14 scope but not the registered rows")
                bad += 1
        progress(f"{len(outside)} units outside the D14 scope: rows checked as copies")
        us = [u for u in us if u not in outside]
    picked: list = []
    if base is not None:
        changed = [u for u in changed_units(mode, base) if u in us]
        rest = [u for u in us if u not in changed]
        picked = sample(rest, k)
        progress(f"changed since {base}: {len(changed)}; sample of the rest: {len(picked)}")
        us = [u for u in us if u in changed or u in picked]
    done = run_units([u for u in us if u not in picked], mode, jobs, progress)
    if picked:
        # the sample is run again, never taken from the cache: its point is to
        # catch a change of the environment that the cache keys do not see
        import tempfile

        saved_parts = verify.PARTS
        with tempfile.TemporaryDirectory(prefix="cobol-equiv-sample-") as d:
            verify.PARTS = Path(d)
            try:
                done.update(run_units(picked, mode, jobs, progress))
            finally:
                verify.PARTS = saved_parts
    selected = {unit_id(u) for u in us}
    if mode == "registered":
        # the D14 scope rests on the static scan: a unit outside it must make
        # no CobDecimal comparison or hash call
        for u in us:
            if u in affected or u in sampled or u[2] == "C":
                continue
            calls = sum(int(r.get(k, 0)) for r in done[u] for k in ("eq", "order", "hash"))
            if calls:
                print(f"{unit_id(u)}: outside the D14 scope but made {calls} CobDecimal comparison or hash calls")
                bad += 1
        committed = _rows_by_unit(out.read_text(encoding="utf-8") if out.exists() else "")
        fields = verify.FIELDS if field == "verdicts" else verify.USAGE_FIELDS
        for u in us:
            if field == "comparisons" and unit_id(u) not in committed:
                continue  # the comparisons files hold the D14 scope only
            rows = done[u] if field == "verdicts" else [r for r in done[u] if r["set"] == "heldout"
                                                      and r["version"] == verify.PRIMARY]
            fresh = io.StringIO()
            w = csv.DictWriter(fresh, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
            old = io.StringIO()
            w = csv.DictWriter(old, fieldnames=fields, lineterminator="\n")
            w.writeheader()
            w.writerows(committed.get(unit_id(u), []))
            diffs = verify.compare(old.getvalue(), fresh.getvalue())
            for d in diffs[:5]:
                print(f"{out.name} {unit_id(u)}: {d}")
            bad += bool(diffs)
    print(f"{len(selected)} units checked ({mode}), {bad} differ")
    return 1 if bad else 0


# ---- the scope of the corrected-mode verification (deviation D14) ------------

D14_SAMPLE = 30
D14_SEED = zlib.crc32(b"d14-sample")


def affected_units() -> list:
    """Units whose translation compares CobDecimal values (==, !=, <, <=, >,
    >=, in) or hashes them, by the static scan (eqscan), and every condition B
    attempt derived from such an A translation."""
    from .eqscan import scan, translations

    hit = set()
    for track, name, cond, attempt, _, path in translations():
        if scan(path.read_text(encoding="utf-8")):
            hit.add((track, name, cond, attempt))
            if cond == "A":
                hit.add((track, name, "B", attempt))  # round 0 of B is the A translation
    return [u for u in verify.units() if u in hit]


def d14_sample(affected: list) -> list:
    """D14_SAMPLE units of conditions A and B outside the affected ones, fixed seed."""
    rest = [u for u in verify.units() if u[2] != "C" and u not in affected]
    picked = set(random.Random(D14_SEED).sample(rest, min(D14_SAMPLE, len(rest))))
    return [u for u in rest if u in picked]


def scope() -> tuple[list, list]:
    """(affected units, sample units) of the corrected-mode verification."""
    affected = affected_units()
    return affected, d14_sample(affected)


def c_uses_runtime() -> list[str]:
    """Condition C translations that mention the runtime package (none may:
    they run with python -I -S, where it cannot be imported, so the
    comparison behaviour of CobDecimal cannot reach them)."""
    from .programs import programs

    out = []
    for track in ("E", "R"):
        for p in programs(track):
            for attempt in (1, 2, 3):
                f = verify.RUNS / track / p.name / "C" / str(attempt) / "translation.py"
                if f.exists() and "cobol_equiv" in f.read_text(encoding="utf-8"):
                    out.append(f.relative_to(verify.ROOT).as_posix())
    return out


def _csv(rows_by_unit: dict, units: list, fields: list) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for u in units:
        w.writerows(rows_by_unit.get(u, []))
    return buf.getvalue()


def _usage(rows: list) -> list:
    return [r for r in rows if r["set"] == "heldout" and r["version"] == verify.PRIMARY]


def sensitivity(jobs: int | None, progress) -> int:
    """Runs the D14 scope in both modes and writes verdicts-corrected.csv
    (the registered rows, with the rows of the scope units replaced by
    their corrected-mode rows), comparisons.csv and comparisons-corrected.csv
    (scope units only) and verify-inputs.json."""
    bad = c_uses_runtime()
    for f in bad:
        print(f"condition C translation mentions the runtime: {f}")
    if bad:
        return 1
    progress("condition C: no translation mentions the runtime package")
    affected, picked = scope()
    us = [u for u in verify.units() if u in affected or u in picked]
    progress(f"scope: {len(affected)} affected units, {len(picked)} sample units")
    reg = run_units(us, "registered", jobs, progress)
    committed = _rows_by_unit(verify.OUT.read_text(encoding="utf-8"))
    status = 0
    for u in us:
        diffs = verify.compare(_csv({u: committed.get(unit_id(u), [])}, [u], verify.FIELDS),
                               _csv(reg, [u], verify.FIELDS))
        if diffs:
            print(f"registered mode does not reproduce verdicts.csv for {unit_id(u)}: {diffs[0]}")
            status = 1
    cor = run_units(us, "corrected", jobs, progress)
    for u in picked:
        diffs = verify.compare(_csv(reg, [u], verify.FIELDS), _csv(cor, [u], verify.FIELDS))
        if diffs:
            print(f"sample unit {unit_id(u)} changes under the corrected runtime: {diffs[0]}")
            status = 1
    all_units = verify.units()
    merged = {u: (cor[u] if u in cor else committed.get(unit_id(u), [])) for u in all_units}
    out_v, out_c = verify.OUTS["corrected"]
    out_v.write_text(_csv(merged, all_units, verify.FIELDS), encoding="utf-8")
    out_c.write_text(_csv({u: _usage(r) for u, r in cor.items()}, us, verify.USAGE_FIELDS), encoding="utf-8")
    verify.OUTS["registered"][1].write_text(_csv({u: _usage(r) for u, r in reg.items()}, us,
                                                 verify.USAGE_FIELDS), encoding="utf-8")
    INPUTS.write_text(json.dumps(inputs_doc(), indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{len(us)} units in both modes; {sum(1 for u in us if u in picked)} sample units")
    return status


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)
    i = sub.add_parser("inputs")
    i.add_argument("--check", action="store_true")
    i.add_argument("--base", help="git ref of the base branch")
    c = sub.add_parser("check")
    c.add_argument("--runtime", choices=verify.MODES, required=True)
    c.add_argument("--track", choices=["E", "R"])
    c.add_argument("--base", help="git ref of the base branch (pull requests)")
    c.add_argument("--sample", type=int, default=2)
    c.add_argument("--jobs", type=int, default=None)
    t = sub.add_parser("sensitivity")
    t.add_argument("--jobs", type=int, default=None)
    a = ap.parse_args(argv)
    progress = lambda m: print(m, file=sys.stderr, flush=True)  # noqa: E731
    if a.command == "inputs":
        doc = inputs_doc()
        text = json.dumps(doc, indent=1, sort_keys=True) + "\n"
        if a.check:
            if not INPUTS.exists():
                print(f"{INPUTS} missing")
                return 1
            base = _git_show(a.base, INPUTS) if a.base else None
            if base:
                old = json.loads(base)
                if old["runtime_version"] == doc["runtime_version"] and \
                        old["runtime_sha256"] != doc["runtime_sha256"]:
                    print("the runtime changed without a new version number (cobol_equiv.runtime.__version__)")
                    return 1
            if INPUTS.read_text(encoding="utf-8") != text:
                print(f"{INPUTS} is not what the committed translations, vectors and runtime give")
                return 1
            print("verify-inputs.json is current")
            return 0
        INPUTS.write_text(text, encoding="utf-8")
        return 0
    if a.command == "sensitivity":
        return sensitivity(a.jobs, progress)
    return check(a.runtime, a.track, a.base, a.sample, a.jobs, progress)


if __name__ == "__main__":
    sys.exit(main())

"""Partial and split re-verification for CI (docs/benchmark.md, "Verification in CI").

    python -m cobol_equiv.benchmark.ci inputs [--check [--base REF]]
    python -m cobol_equiv.benchmark.ci check --runtime MODE [--track T] [--base REF --sample K] [--jobs N]

A full verification of one runtime mode takes hours, so CI does not run
both modes on every pull request:

- `inputs` writes benchmark/results/verify-inputs.json: for each runtime mode
  and unit (track, program, condition, attempt), the SHA-256 of what decides
  its verdicts: the translation files of the unit, the vectors file, the
  runtime mode and, for conditions A and B, the runtime version. It also
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


def runtime_version() -> str:
    from .. import runtime

    return runtime.__version__


def input_hash(unit, mode: str) -> str:
    track, name, condition, attempt = unit
    p = verify._program(track, name)
    runtime = "none" if condition == "C" else f"{mode}|{runtime_version()}"
    h = hashlib.sha256(f"{track}|{name}|{condition}|{attempt}|{runtime}".encode("utf-8"))
    h.update(vectors_path(p).read_bytes())
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
    from those on the git ref base (all units when base has no record)."""
    old_inputs = _git_show(base, INPUTS)
    old = json.loads(old_inputs)["units"].get(mode, {}) if old_inputs else {}
    out_v, out_c = verify.OUTS[mode]
    rows_old = [_rows_by_unit(_git_show(base, out_v)), _rows_by_unit(_git_show(base, out_c))]
    rows_new = [_rows_by_unit(f.read_text(encoding="utf-8") if f.exists() else "") for f in (out_v, out_c)]
    changed = []
    for u in verify.units():
        i = unit_id(u)
        if old.get(i) != input_hash(u, mode) or any(a.get(i) != b.get(i) for a, b in zip(rows_old, rows_new)):
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


def run_units(units: list, mode: str, jobs: int | None, progress) -> dict:
    done = {u: r for u in units if (r := verify._saved(u, mode)) is not None}
    todo = [u for u in units if u not in done]
    progress(f"{len(units)} units ({mode}): {len(done)} saved, {len(todo)} to run")
    phases = [[u for u in todo if u[2] != "B"], [u for u in todo if u[2] == "B"]]
    i = 0
    with ProcessPoolExecutor(max_workers=jobs or os.cpu_count() or 1) as ex:
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
    bad = 0
    for out, field in zip(verify.OUTS[mode], ("verdicts", "comparisons")):
        committed = _rows_by_unit(out.read_text(encoding="utf-8") if out.exists() else "")
        fields = verify.FIELDS if field == "verdicts" else verify.USAGE_FIELDS
        for u in us:
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
    return check(a.runtime, a.track, a.base, a.sample, a.jobs, progress)


if __name__ == "__main__":
    sys.exit(main())

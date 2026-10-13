"""Materialise the benchmark vectors of a program (docs/benchmark-protocol.md,
section 2) and their expected outputs.

    python -m cobol_equiv.benchmark.vectors [--programs a,b] [--track E,R]

For each program of both tracks this writes
`benchmark/vectors/<track>/<name>.json.gz` (gzip, fixed header, so the bytes
are reproducible):

    {"program": name, "track": "E" | "R", "hypothesis": version,
     "sets": {"visible": [...], "dev": [...], "heldout": [...]},
     "removed": [{"set", "source", "input", "reason"}]}

Each vector is {"source": "generated 17" | "fixed 2" | "boundary 3",
"input": {name: base64}, "expected": {cobc version label: {"stdout":
base64, "files": {name: base64 | null}}}}. Inputs are generated once, in
generation order, and never again during scoring. An input identical to an
earlier one in any set is dropped. An input on which the COBOL program
exits with a non-zero status or times out (on GnuCOBOL 3.1.2) is removed
and listed.

Expected outputs are recorded for the compiler selected by COBC; run the
command once per compiler version (3.1.2 first, it decides the sets).
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import sys
import zlib
from pathlib import Path

from ..cobc import version_label
from ..harness.boundary import boundary_vectors
from ..harness.cobol import BUILD_DIR, CobolError, compile_program, run_program
from ..harness.spec import STDIN, ProgramSpec
from .programs import Program, programs

ROOT = Path(__file__).resolve().parents[3]
VECTORS_DIR = ROOT / "benchmark" / "vectors"
N_DEV = 50
N_HELDOUT = 200
N_VISIBLE = 2
PRIMARY = "3.1.2"


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def unb64(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


def seed_of(text: str) -> int:
    return zlib.crc32(text.encode("utf-8"))


def generated_inputs(spec: ProgramSpec, seed_text: str, n: int) -> list[dict]:
    """Up to n inputs from the spec's generators, in generation order, with
    the seed crc32(seed_text). Hypothesis 6.169.0 (requirements-repro.txt)."""
    from hypothesis import HealthCheck, given, seed, settings

    from ..harness.strategies import inputs as inputs_strategy

    if not spec.inputs:
        return []
    got: list[dict] = []

    @seed(seed_of(seed_text))
    @settings(max_examples=n, database=None, deadline=None, suppress_health_check=list(HealthCheck),
              print_blob=False)
    @given(inputs_strategy(spec.inputs))
    def collect(inp):
        got.append(dict(inp))

    collect()
    return got


def _key(inp: dict) -> tuple:
    return tuple(sorted((k, bytes(v)) for k, v in inp.items()))


def _nonempty(inp: dict) -> bool:
    return bool(inp) and all(v for v in inp.values())


def build_sets(spec: ProgramSpec) -> dict[str, list[tuple[str, dict]]]:
    seen: set = set()

    def take(items, limit=None):
        out = []
        for source, inp in items:
            k = _key(inp)
            if k in seen:
                continue
            seen.add(k)
            out.append((source, inp))
            if limit is not None and len(out) >= limit:
                break
        return out

    vis = [(f"generated {i}", g) for i, g in enumerate(generated_inputs(spec, "visible:" + spec.name, 50), 1)
           if _nonempty(g)]
    visible = take(vis, N_VISIBLE)
    dev = take([(f"fixed {i}", v) for i, v in enumerate(spec.vectors, 1)]
               + [(f"generated {i}", g) for i, g in enumerate(generated_inputs(spec, "dev:" + spec.name, N_DEV), 1)])
    held = take([(f"generated {i}", g) for i, g in enumerate(generated_inputs(spec, spec.name, N_HELDOUT), 1)]
                + [(f"boundary {i}", b) for i, b in enumerate(boundary_vectors(spec.inputs), 1)])
    return {"visible": visible, "dev": dev, "heldout": held}


def expected_output(spec: ProgramSpec, exe: Path, inp: dict) -> dict:
    stdin = inp.get(STDIN, b"")
    files = {k: v for k, v in inp.items() if k != STDIN}
    res = run_program(exe, stdin, files, spec.outputs, spec.timeout)
    if res.returncode != 0:
        raise CobolError(f"exit status {res.returncode}: {res.stderr.decode('utf-8', 'replace')[:200]}")
    return {"stdout": b64(res.stdout),
            "files": {k: (None if v is None else b64(v)) for k, v in res.files.items()}}


def encode_input(inp: dict) -> dict:
    return {k: b64(v) for k, v in inp.items()}


def decode_input(enc: dict) -> dict:
    return {k: unb64(v) for k, v in enc.items()}


def vectors_path(p: Program) -> Path:
    return VECTORS_DIR / p.track / f"{p.name}.json.gz"


def load(p: Program) -> dict:
    return json.loads(gzip.decompress(vectors_path(p).read_bytes()).decode("utf-8"))


def materialise(p: Program) -> dict:
    """Build the sets and the GnuCOBOL 3.1.2 outputs (the primary version)."""
    spec = p.spec()
    exe = compile_program(spec.source, BUILD_DIR, spec.free_format)
    label = version_label()
    sets = build_sets(spec)
    doc = {"program": p.name, "track": p.track, "hypothesis": _hypothesis_version(),
           "sets": {}, "removed": []}
    for name, items in sets.items():
        kept = []
        for source, inp in items:
            try:
                exp = expected_output(spec, exe, inp)
            except CobolError as e:
                doc["removed"].append({"set": name, "source": source, "input": encode_input(inp),
                                       "reason": str(e)[:200]})
                continue
            kept.append({"source": source, "input": encode_input(inp), "expected": {label: exp}})
        doc["sets"][name] = kept
    return doc


def add_version(p: Program, doc: dict) -> dict:
    """Add the expected outputs of the selected (secondary) compiler."""
    spec = p.spec()
    exe = compile_program(spec.source, BUILD_DIR, spec.free_format)
    label = version_label()
    for items in doc["sets"].values():
        for v in items:
            try:
                v["expected"][label] = expected_output(spec, exe, decode_input(v["input"]))
            except CobolError as e:
                v["expected"][label] = {"error": str(e)[:200]}
    return doc


def _hypothesis_version() -> str:
    import hypothesis
    return hypothesis.__version__


def write(p: Program, doc: dict) -> None:
    path = vectors_path(p)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(doc, indent=1, sort_keys=True) + "\n").encode("utf-8")
    path.write_bytes(gzip.compress(data, compresslevel=9, mtime=0))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--programs", default="", help="comma-separated names (default: all)")
    ap.add_argument("--track", default="E,R", help="comma-separated tracks (T: runner test program)")
    a = ap.parse_args(argv)
    names = [n for n in a.programs.split(",") if n]
    label = version_label()
    for p in [p for t in a.track.split(",") for p in programs(t)]:
        if names and p.name not in names:
            continue
        if label == PRIMARY:
            doc = materialise(p)
        else:
            doc = add_version(p, load(p))
        write(p, doc)
        n = {k: len(v) for k, v in doc["sets"].items()}
        print(f"{p.track} {p.name:40} {n} removed {len(doc['removed'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

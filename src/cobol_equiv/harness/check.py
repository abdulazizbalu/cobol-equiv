"""Differential check of one translation against GnuCOBOL.

    python -m cobol_equiv.harness.check corpus/loancalc path/to/translation.py [--examples N]

1. Every fixed regression vector of the program spec is run.
2. Then N inputs are generated with Hypothesis and run; a failing input is
   shrunk to a smaller one. The generation is seeded from the program name
   only (no example database), so every translation of a program, and every
   run, gets the same inputs, independent of the harness code and of what ran
   earlier in the process.

The first difference is reported as stream, line and field name (when the
spec has an output layout), with the expected (GnuCOBOL) and actual bytes.
An exception or a timeout in the translation counts as a difference. A
translation that triggers the runtime's Unsupported error (even if it catches
it, while running or while its module is imported by load_module /
load_module_from_source) is reported as UNSUPPORTED, exit status 2: never as
a pass. Not covered: errors raised in another thread or process.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import signal
import sys
import types
import zlib
from dataclasses import dataclass, field
from pathlib import Path

from ..runtime.errors import Unsupported, reset_unsupported_hits, unsupported_hits
from .cobol import BUILD_DIR, CobolError, compile_program, run_program
from .compare import Difference, compare
from .spec import STDIN, ProgramSpec


class TranslationTimeout(BaseException):
    """BaseException so that a broad `except Exception` in a translation
    cannot swallow the time limit."""


@contextlib.contextmanager
def time_limit(seconds: float):
    """SIGALRM-based limit; a no-op where unavailable (non-POSIX, non-main thread)."""
    try:
        old = signal.signal(signal.SIGALRM, _raise_timeout)
    except (ValueError, AttributeError):
        yield
        return
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)


def _raise_timeout(signum, frame):
    raise TranslationTimeout()


@dataclass
class CheckResult:
    program: str
    vectors: int = 0
    vectors_passed: int = 0
    generated: int = 0
    difference: Difference | None = None
    failing_input: dict | None = None
    failing_source: str = ""  # "vector N" or "generated"
    notes: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.difference is None

    @property
    def status(self) -> str:
        """'pass', 'fail', or 'unsupported' (the translation hit a runtime
        feature outside the supported subset; never counted as a pass)."""
        if self.difference is None:
            return "pass"
        return "unsupported" if self.difference.unsupported else "fail"


IMPORT_HITS = "__cobol_equiv_unsupported_at_import__"


def _caught(n: int, extra: str = "") -> Difference:
    return Difference("<translation>", 0, 0, None, b"", b"",
                      f"hit an unsupported runtime feature {n} time(s) and caught the error{extra}",
                      unsupported=True)


def import_hits(module: types.ModuleType) -> int:
    """Unsupported errors raised while load_module / load_module_from_source
    imported `module` (including modules it imported)."""
    return getattr(module, IMPORT_HITS, 0)


def run_once(spec: ProgramSpec, exe: Path, main, inputs: dict[str, bytes],
             hits_at_import: int | None = None) -> Difference | None:
    """hits_at_import: import_hits() of the module the translation was
    loaded from; if None, it is looked up in the globals of `main`."""
    stdin = inputs.get(STDIN, b"")
    files = {k: v for k, v in inputs.items() if k != STDIN}
    res = run_program(exe, stdin, files, spec.outputs, spec.timeout)
    if res.returncode != 0:
        raise CobolError(f"COBOL program exited with {res.returncode}: "
                         f"{res.stderr.decode('utf-8', 'replace')[:500]}")
    reset_unsupported_hits()
    try:
        with time_limit(spec.timeout):
            out, out_files = main(stdin, dict(files))
    except TranslationTimeout:
        return Difference("<translation>", 0, 0, None, b"", b"", f"timed out after {spec.timeout}s")
    except KeyboardInterrupt:
        raise
    except Unsupported as e:
        return Difference("<translation>", 0, 0, None, b"", b"",
                          f"hit an unsupported runtime feature: {e}", unsupported=True)
    except BaseException as e:  # any crash, including sys.exit(), is a detected difference
        if unsupported_hits():
            return _caught(unsupported_hits(), f", then raised {type(e).__name__}: {e}")
        return Difference("<translation>", 0, 0, None, b"", b"", f"raised {type(e).__name__}: {e}")
    if unsupported_hits():
        # the translation caught an Unsupported error and carried on: its
        # output is not trusted even if it happens to match
        return _caught(unsupported_hits())
    at_import = (hits_at_import if hits_at_import is not None
                 else getattr(main, "__globals__", {}).get(IMPORT_HITS, 0))
    if at_import:
        return _caught(at_import, " while its module was imported")
    return compare(res.stdout, res.files, out, out_files or {}, spec.outputs, spec.layouts)


def check(spec: ProgramSpec, main, examples: int = 100, build_dir: Path | None = None,
          hits_at_import: int | None = None) -> CheckResult:
    from hypothesis import HealthCheck, given, seed, settings

    from .strategies import inputs as inputs_strategy
    from .strategies import no_local_constants

    exe = compile_program(spec.source, build_dir or BUILD_DIR, spec.free_format)
    result = CheckResult(spec.name, vectors=len(spec.vectors))
    for i, vec in enumerate(spec.vectors, 1):
        d = run_once(spec, exe, main, vec, hits_at_import)
        if d:
            result.difference, result.failing_input, result.failing_source = d, vec, f"vector {i}"
            return result
        result.vectors_passed += 1
    if examples <= 0 or not spec.inputs:
        return result

    found: dict = {}
    counter = [0]

    @seed(zlib.crc32(spec.name.encode("utf-8")))
    @settings(max_examples=examples, database=None, deadline=None,
              suppress_health_check=list(HealthCheck), print_blob=False)
    @given(inputs_strategy(spec.inputs))
    def prop(inp):
        counter[0] += 1
        d = run_once(spec, exe, main, inp, hits_at_import)
        if d:
            found["diff"], found["input"] = d, inp
            raise AssertionError(d.describe())

    try:
        with no_local_constants():
            prop()
    except AssertionError:
        pass
    result.generated = counter[0]
    if found:
        result.difference, result.failing_input = found["diff"], found["input"]
        result.failing_source = "generated"
    return result


def check_boundary(spec: ProgramSpec, main, build_dir: Path | None = None,
                   hits_at_import: int | None = None):
    """Run the PICTURE-derived boundary vectors (harness/boundary.py).
    Returns (number of vectors, index of the first failing vector or None,
    Difference or None)."""
    from .boundary import boundary_vectors

    exe = compile_program(spec.source, build_dir or BUILD_DIR, spec.free_format)
    vecs = boundary_vectors(spec.inputs)
    for i, v in enumerate(vecs, 1):
        d = run_once(spec, exe, main, v, hits_at_import)
        if d:
            return len(vecs), i, d
    return len(vecs), None, None


def load_module(path: Path, name: str = "translation") -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    reset_unsupported_hits()
    spec.loader.exec_module(mod)
    setattr(mod, IMPORT_HITS, unsupported_hits())
    return mod


def load_module_from_source(source: str, name: str, filename: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    mod.__file__ = filename
    reset_unsupported_hits()
    exec(compile(source, filename, "exec"), mod.__dict__)  # noqa: S102 (corpus code)
    setattr(mod, IMPORT_HITS, unsupported_hits())
    return mod


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("program_dir", help="corpus directory containing spec.py")
    ap.add_argument("translation", help="Python file exposing main(stdin, input_files)")
    ap.add_argument("--examples", type=int, default=100)
    a = ap.parse_args(argv)
    pspec = load_module(Path(a.program_dir) / "spec.py", "program_spec").SPEC
    tr = load_module(Path(a.translation))
    r = check(pspec, tr.main, a.examples, hits_at_import=import_hits(tr))
    print(f"{r.program}: vectors {r.vectors_passed}/{r.vectors}, generated inputs run: {r.generated}")
    if r.passed:
        print("PASS: no difference found")
        return 0
    label = "UNSUPPORTED" if r.status == "unsupported" else "FAIL"
    print(f"{label} ({r.failing_source}): {r.difference.describe()}")
    if r.failing_input is not None:
        for k, v in r.failing_input.items():
            print(f"  input {k}: {v!r}")
    return 2 if r.status == "unsupported" else 1


if __name__ == "__main__":
    sys.exit(main())

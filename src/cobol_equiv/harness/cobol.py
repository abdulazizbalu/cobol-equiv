"""Compiling and running the COBOL side with GnuCOBOL.

Compile: `cobc -x -std=default` (cobol_equiv.cobc.COBC_FLAGS), with every
inherited COB* environment variable removed. Binaries are cached under
.cobol-build/ keyed by a hash of the source and the cobc version.

Run: in a fresh temporary directory containing the input files, with the
given stdin, a timeout, and LC_ALL=C. Output files are read back from that
directory.

Determinism: sources that read the clock or random numbers are rejected
before compiling (CURRENT-DATE, WHEN-COMPILED, RANDOM, ACCEPT ... FROM DATE /
DAY / TIME / DAY-OF-WEEK).
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ..cobc import COBC_FLAGS, clean_env, cobc_path, cobc_version

BUILD_DIR = Path(".cobol-build") / "programs"

_NONDETERMINISTIC = re.compile(
    r"CURRENT-DATE|WHEN-COMPILED|\bRANDOM\b|ACCEPT\s+[\w-]+\s+FROM\s+(DATE|DAY|TIME|DAY-OF-WEEK)\b",
    re.IGNORECASE,
)


class CobolError(RuntimeError):
    pass


def check_deterministic(source: str) -> None:
    for n, line in enumerate(source.splitlines(), 1):
        code = line[6:72] if len(line) > 6 else ""
        if code[:1] in ("*", "/"):
            continue
        m = _NONDETERMINISTIC.search(code)
        if m:
            raise CobolError(f"line {n}: non-deterministic construct {m.group(0)!r} is not allowed")


def check_fixed_format(source: str) -> None:
    """Fixed-format COBOL ignores columns 73-80; text there is silently lost."""
    long = [n for n, line in enumerate(source.splitlines(), 1) if len(line) > 72]
    if long:
        raise CobolError(f"lines longer than 72 columns (fixed format): {long}")


def compile_program(source: Path, build_dir: Path = BUILD_DIR) -> Path:
    text = source.read_text(encoding="utf-8")
    check_fixed_format(text)
    check_deterministic(text)
    digest = hashlib.sha256((cobc_version() + "\0" + text).encode("utf-8")).hexdigest()[:16]
    build_dir.mkdir(parents=True, exist_ok=True)
    exe = build_dir / f"{source.stem}-{digest}"
    if exe.exists():
        return exe
    tmp = exe.with_suffix(".tmp")
    r = subprocess.run([cobc_path(), *COBC_FLAGS, "-o", str(tmp), str(source)],
                       capture_output=True, env=clean_env())
    if r.returncode != 0:
        raise CobolError(f"cobc failed for {source}:\n{r.stderr.decode('utf-8', 'replace')}")
    tmp.replace(exe)
    return exe


@dataclass
class RunResult:
    stdout: bytes
    files: dict[str, bytes | None]
    returncode: int
    stderr: bytes


def run_program(exe: Path, stdin: bytes, input_files: dict[str, bytes], output_files: list[str],
                timeout: float = 10.0) -> RunResult:
    with tempfile.TemporaryDirectory(prefix="cobol-equiv-") as d:
        wd = Path(d)
        for name, data in input_files.items():
            (wd / name).write_bytes(data)
        try:
            r = subprocess.run([str(exe.resolve())], input=stdin, capture_output=True,
                               cwd=wd, env=clean_env(), timeout=timeout)
        except subprocess.TimeoutExpired as e:
            raise CobolError(f"COBOL program timed out after {timeout}s") from e
        files = {}
        for name in output_files:
            p = wd / name
            files[name] = p.read_bytes() if p.exists() else None
        return RunResult(r.stdout, files, r.returncode, r.stderr)

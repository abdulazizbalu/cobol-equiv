"""Run a translation on materialised vectors in a child process and compare
the results with the expected outputs (docs/benchmark-protocol.md, section 4).

Conditions A and B run with this virtual environment's Python (`-I`);
condition C with `python3.12 -I -S`, so only the standard library can be
imported. The child receives only the inputs. Limits: the spec's timeout per
vector, 600 s in total, 2 GiB of address space.
"""

from __future__ import annotations

import json
import resource
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ..harness.compare import Difference, compare
from ..harness.spec import STDIN, ProgramSpec
from .vectors import b64, unb64

DRIVER = Path(__file__).with_name("_driver.py")
TOTAL_LIMIT = 600
MEMORY_LIMIT = 2 * 1024 ** 3
STDLIB_PYTHON = "python3.12"


def _limits():
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT, MEMORY_LIMIT))


def python_for(condition: str) -> list[str]:
    if condition == "C":
        return [STDLIB_PYTHON, "-I", "-S"]
    return [sys.executable, "-I"]


def run_translation(path: Path, inputs: list[dict], timeout: float, condition: str) -> list[dict]:
    """Per input: {"stdout", "files"} (base64) or {"error"} or {"timeout"},
    each with "unsupported" (number of Unsupported errors raised)."""
    req = {"module": str(path.resolve()), "timeout": timeout,
           "vectors": [{"stdin": b64(inp.get(STDIN, b"")),
                        "files": {k: b64(v) for k, v in inp.items() if k != STDIN}} for inp in inputs]}
    with tempfile.TemporaryDirectory(prefix="cobol-equiv-run-") as d:
        rq, rs = Path(d) / "request.json", Path(d) / "result.json"
        rq.write_text(json.dumps(req), encoding="utf-8")
        try:
            subprocess.run([*python_for(condition), str(DRIVER), str(rq), str(rs)], cwd=d,
                           stdin=subprocess.DEVNULL, capture_output=True, timeout=TOTAL_LIMIT,
                           preexec_fn=_limits)
        except subprocess.TimeoutExpired:
            return [{"timeout": True, "total": True, "unsupported": 0} for _ in inputs]
        if not rs.exists():
            return [{"error": "the translation process ended without a result", "unsupported": 0}
                    for _ in inputs]
        results = json.loads(rs.read_text(encoding="utf-8"))["results"]
    return results


@dataclass
class Verdict:
    passed: bool
    kind: str  # "pass", "difference", "unsupported", "error", "timeout"
    detail: str = ""
    difference: Difference | None = None


UNSUPPORTED_ERRORS = ("Unsupported:", "MoveError:", "PicError:", "DataError:")


def judge(spec: ProgramSpec, expected: dict, result: dict) -> Verdict:
    if "error" in result and result["error"].startswith(UNSUPPORTED_ERRORS):
        return Verdict(False, "unsupported", result["error"])
    if result.get("unsupported"):
        return Verdict(False, "unsupported",
                       f"hit an unsupported runtime feature {result['unsupported']} time(s)")
    if result.get("timeout"):
        return Verdict(False, "timeout", "timed out")
    if "error" in result:
        return Verdict(False, "error", result["error"])
    exp_out = unb64(expected["stdout"])
    exp_files = {k: (None if v is None else unb64(v)) for k, v in expected["files"].items()}
    act_out = unb64(result["stdout"])
    act_files = {k: unb64(v) for k, v in result["files"].items()}
    d = compare(exp_out, exp_files, act_out, act_files, spec.outputs, spec.layouts)
    if d is None:
        return Verdict(True, "pass")
    return Verdict(False, "difference", d.describe(), d)

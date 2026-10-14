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
EXTENDED_TIMEOUT = 120  # per vector, for vectors that exceeded the protocol's limits (D12)
EXTENDED_TOTAL = 7200
EXTENDED_MAX_TIMEOUTS = 3  # the extended run stops after this many vectors time out again
MEMORY_LIMIT = 2 * 1024 ** 3
STDLIB_PYTHON = "python3.12"


def _limits():
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT, MEMORY_LIMIT))


def python_for(condition: str) -> list[str]:
    if condition == "C":
        return [STDLIB_PYTHON, "-I", "-S"]
    return [sys.executable, "-I"]


def run_translation(path: Path, inputs: list[dict], timeout: float, condition: str,
                    total: float = TOTAL_LIMIT, max_timeouts: int | None = None,
                    runtime: str | None = None) -> list[dict]:
    """Per input: {"stdout", "files"} (base64) or {"error"} or {"timeout"},
    each with "unsupported" (number of Unsupported errors raised) and "cmp"
    (CobDecimal comparison calls, counted when `runtime`, "registered" or
    "corrected", is given; see _driver.py). Vectors not
    reached before the total time limit get {"timeout": True, "total": True};
    the results of the vectors finished before it are kept."""
    req = {"module": str(path.resolve()), "timeout": timeout, "max_timeouts": max_timeouts,
           "runtime": runtime,
           "vectors": [{"stdin": b64(inp.get(STDIN, b"")),
                        "files": {k: b64(v) for k, v in inp.items() if k != STDIN}} for inp in inputs]}
    with tempfile.TemporaryDirectory(prefix="cobol-equiv-run-") as d, \
            tempfile.TemporaryDirectory(prefix="cobol-equiv-io-") as io_dir:
        # the request and result files are outside the child's working directory
        rq, rs = Path(io_dir) / "request.json", Path(io_dir) / "result.json"
        rq.write_text(json.dumps(req), encoding="utf-8")
        stopped = False
        try:
            subprocess.run([*python_for(condition), str(DRIVER), str(rq), str(rs)], cwd=d,
                           stdin=subprocess.DEVNULL, capture_output=True, timeout=total,
                           preexec_fn=_limits)
        except subprocess.TimeoutExpired:
            stopped = True
        results, abandoned = [], False
        if rs.exists():
            for line in rs.read_text(encoding="utf-8").splitlines():
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    break  # a line cut by the stop
                if r.get("abandoned"):
                    abandoned = True
                    break
                results.append(r)
    if len(results) > len(inputs):
        return [{"error": "the result file has more results than inputs", "unsupported": 0}
                for _ in inputs]
    missing = len(inputs) - len(results)
    if missing:
        if stopped:
            fill = {"timeout": True, "total": True, "unsupported": 0}
        elif abandoned:
            fill = {"timeout": True, "abandoned": True, "unsupported": 0}
        elif max_timeouts and sum(1 for r in results if r.get("timeout")) >= max_timeouts:
            fill = {"timeout": True, "not_rerun": True, "unsupported": 0}
        else:
            fill = {"error": "the translation process ended without a result", "unsupported": 0}
        results += [dict(fill) for _ in range(missing)]
    return results


def run_extended(path: Path, inputs: list[dict], timeout: float, condition: str,
                 runtime: str | None = None) -> list[dict]:
    """run_translation with the protocol's limits; vectors that exceed them
    are run again with EXTENDED_TIMEOUT per vector and EXTENDED_TOTAL in total
    (deviation D12). A vector that finishes there gets "slow": True; one that
    still exceeds the limits stays a timeout. After EXTENDED_MAX_TIMEOUTS such
    vectors the extended run stops; the late vectors not run again stay
    timeouts ("not_rerun": True)."""
    results = run_translation(path, inputs, timeout, condition, runtime=runtime)
    late = [i for i, r in enumerate(results) if r.get("timeout")]
    if late:
        again = run_translation(path, [inputs[i] for i in late], EXTENDED_TIMEOUT, condition,
                                total=EXTENDED_TOTAL, max_timeouts=EXTENDED_MAX_TIMEOUTS,
                                runtime=runtime)
        for i, r in zip(late, again):
            if not r.get("timeout"):
                r["slow"] = True
            results[i] = r
    return results


@dataclass
class Verdict:
    passed: bool
    kind: str  # "pass", "difference", "unsupported", "error", "timeout", "no expected output"
    detail: str = ""
    difference: Difference | None = None


UNSUPPORTED_ERRORS = ("Unsupported:", "MoveError:", "PicError:", "DataError:")


def judge(spec: ProgramSpec, expected: dict, result: dict) -> Verdict:
    if "error" in expected:  # the COBOL program failed on this input (secondary compiler only)
        return Verdict(False, "no expected output", expected["error"])
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

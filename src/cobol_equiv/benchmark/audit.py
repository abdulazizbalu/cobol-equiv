"""Consistency check of the committed translation artifacts.

    python -m cobol_equiv.benchmark.audit

For every call under benchmark/runs/{E,R}/ it checks that
- the configured model and the client version are those frozen in
  benchmark/manifest.json, and the reply reports only that model;
- prompt.md of a one-shot call is byte-identical to the prompt rebuilt now
  from the committed sources, vectors and API sheet (and the sheet's
  SHA-256 is the one in the manifest);
- translation.py is exactly the code extracted from reply.json;
- every program has the attempts 1-3 of A, B and C, and each B attempt's
  final.json matches its round directories;
and lists translations whose code touches the file system, processes or
the interpreter's arguments (protocol, notes on the child process).
Exit status 1 if any check fails.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

from .programs import programs
from .prompts import SHEET, prompt_one_shot
from .translate import extract_code

ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "benchmark" / "runs"
MANIFEST = ROOT / "benchmark" / "manifest.json"
SUSPECT = re.compile(r"\bopen\(|\bos\.|\bpathlib\b|\bsys\.argv\b|\bsubprocess\b|__file__|\bimportlib\b|"
                     r"\bglob\b|\bshutil\b|\bsocket\b")


def check() -> tuple[list[str], list[str], dict]:
    frozen = json.loads(MANIFEST.read_text(encoding="utf-8"))["frozen_before_first_call"]
    problems, suspects = [], []
    counts = {"calls": 0, "prompts_rebuilt": 0}
    if hashlib.sha256(SHEET.read_bytes()).hexdigest() != frozen["api_sheet_sha256"]:
        problems.append("API sheet SHA-256 differs from the manifest")
    for track in ("E", "R"):
        for p in programs(track):
            base = RUNS / track / p.name
            for cond in ("A", "B", "C"):
                for attempt in (1, 2, 3):
                    d = base / cond / str(attempt)
                    if cond == "B":
                        if not (d / "final.json").exists():
                            problems.append(f"{d}: missing final.json")
                            continue
                        calls = sorted(d.glob("round-*/call.json"))
                        _check_final(d, base, attempt, calls, problems)
                    else:
                        calls = [d / "call.json"]
                        if not calls[0].exists():
                            problems.append(f"{d}: missing")
                            continue
                        expected = prompt_one_shot(p, cond)
                        counts["prompts_rebuilt"] += 1
                        if (d / "prompt.md").read_text(encoding="utf-8") != expected:
                            problems.append(f"{d}: prompt.md differs from the rebuilt prompt")
                    for c in calls:
                        counts["calls"] += 1
                        _check_call(c.parent, frozen, problems, suspects)
    return problems, suspects, counts


def _check_final(d: Path, base: Path, attempt: int, calls: list, problems: list) -> None:
    """final.json names the last version with code, and its rounds are the
    round directories."""
    fin = json.loads((d / "final.json").read_text(encoding="utf-8"))
    if [r["round"] for r in fin["rounds"]] != list(range(1, len(calls) + 1)):
        problems.append(f"{d}: final.json rounds do not match the round directories")
    current = base / "A" / str(attempt) / "translation.py"
    current = current if current.exists() else None
    for c in calls:
        if (c.parent / "translation.py").exists():
            current = c.parent / "translation.py"
    expected = None if current is None else current.relative_to(ROOT).as_posix()
    if fin["final"] != expected:
        problems.append(f"{d}: final.json names {fin['final']}, expected {expected}")


def _check_call(d: Path, frozen: dict, problems: list, suspects: list) -> None:
    meta = json.loads((d / "call.json").read_text(encoding="utf-8"))
    if meta["model_id_configured"] != frozen["model_id"]:
        problems.append(f"{d}: configured model {meta['model_id_configured']}")
    if meta["model_ids_reported"] != [frozen["model_id"]]:
        problems.append(f"{d}: reported models {meta['model_ids_reported']}")
    if meta["client_version"] != frozen["client_version"]:
        problems.append(f"{d}: client version {meta['client_version']}")
    reply = json.loads((d / "reply.json").read_text(encoding="utf-8"))
    if sorted(reply.get("modelUsage", {})) != [frozen["model_id"]]:
        problems.append(f"{d}: reply.json modelUsage {sorted(reply.get('modelUsage', {}))}")
    code = extract_code(reply.get("result"))
    t = d / "translation.py"
    if (code is None) != (not t.exists()) or (code is not None and t.read_text(encoding="utf-8") != code):
        problems.append(f"{d}: translation.py is not the code extracted from reply.json")
    if code is not None and SUSPECT.search(code):
        suspects.append(f"{d.relative_to(ROOT).as_posix()}: {sorted(set(SUSPECT.findall(code)))}")


def main() -> int:
    problems, suspects, counts = check()
    print(json.dumps(counts))
    for x in problems:
        print("PROBLEM", x)
    for x in suspects:
        print("REVIEW", x)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

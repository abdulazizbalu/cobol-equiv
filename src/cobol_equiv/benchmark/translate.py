"""Generate translations (docs/benchmark-protocol.md, sections 3 and 7).

    python -m cobol_equiv.benchmark.translate --condition A|C --attempt N [--programs a,b] [--track T]
    python -m cobol_equiv.benchmark.translate --condition B --attempt N [--programs a,b]

Each call runs the Claude Code client non-interactively in an empty
temporary directory with an empty home directory and no tools. For every
call the prompt, the raw JSON reply, the extracted code and a record (UTC
time, model IDs reported, client version, retries) are written under
benchmark/runs/<track>/<program>/<condition>/<attempt>/ (condition B:
round-<k>/ below that). A call whose artifacts exist is not repeated, so an
interrupted run can be resumed.

Generation is not reproducible; verification of the committed translations
is (cobol_equiv.benchmark.verify).
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from .programs import Program, programs
from .prompts import feedback, prompt_one_shot, prompt_repair
from .runner import Verdict, judge, run_translation
from .vectors import PRIMARY, decode_input, load

ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "benchmark" / "runs"
MANIFEST = ROOT / "benchmark" / "manifest.json"
SYSTEM_PROMPT = "You are a careful software engineer."
CALL_TIMEOUT = 1800
MAX_RETRIES = 5
REPAIR_ROUNDS = 3
# The only environment variables passed to the client: the executable
# path, the locale, the network proxy and its certificates, and the API
# endpoint. Everything else (session, effort, extra directories, skills,
# plugins) is left out, so a call does not depend on the session that starts
# this script and runs with the client's default settings.
ENV_ALLOWLIST = ("PATH", "LANG", "LC_ALL", "HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy",
                 "NO_PROXY", "no_proxy", "SSL_CERT_FILE", "NODE_EXTRA_CA_CERTS", "REQUESTS_CA_BUNDLE",
                 "CURL_CA_BUNDLE", "ANTHROPIC_BASE_URL")


def client_env(home: str) -> dict:
    env = {k: os.environ[k] for k in ENV_ALLOWLIST if k in os.environ}
    env["HOME"] = home
    return env


class RunStopped(RuntimeError):
    """A call kept reporting a model ID other than the configured one."""


def configured_model() -> str:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["frozen_before_first_call"]["model_id"]


def client_command(model: str) -> list[str]:
    return ["claude", "-p", "--model", model, "--safe-mode", "--setting-sources", "",
            "--tools", "", "--disallowedTools", "mcp__*", "--strict-mcp-config",
            "--mcp-config", '{"mcpServers":{}}', "--system-prompt", SYSTEM_PROMPT,
            "--no-session-persistence", "--disable-slash-commands", "--output-format", "json"]


def client_version() -> str:
    r = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=60)
    return r.stdout.strip()


def call_once(prompt: str, model: str) -> tuple[str, dict | None, str]:
    """One client run. Returns (raw stdout, parsed JSON or None, problem)."""
    with tempfile.TemporaryDirectory(prefix="translate-cwd-") as cwd, \
            tempfile.TemporaryDirectory(prefix="translate-home-") as home:
        env = client_env(home)
        try:
            r = subprocess.run(client_command(model), input=prompt.encode("utf-8"), cwd=cwd, env=env,
                               capture_output=True, timeout=CALL_TIMEOUT)
        except subprocess.TimeoutExpired:
            return "", None, "client timed out"
    raw = r.stdout.decode("utf-8", "replace")
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError:
        return raw, None, f"no JSON result (exit status {r.returncode}): " + r.stderr.decode("utf-8", "replace")[:300]
    if doc.get("is_error") or doc.get("subtype") != "success":
        return raw, doc, f"client reported an error: {doc.get('subtype')}"
    return raw, doc, ""


def call(prompt: str, model: str) -> dict:
    """A call with the protocol's retries. Returns the record of the call."""
    attempts = []
    transport_failures = model_failures = 0
    while True:
        started = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        raw, doc, problem = call_once(prompt, model)
        models = sorted((doc or {}).get("modelUsage", {}))
        entry = {"started_utc": started, "model_ids": models, "problem": problem}
        if not problem and models != [model]:
            entry["problem"] = f"reported model IDs {models}, configured {model}"
            model_failures += 1
            attempts.append(entry)
            if model_failures > MAX_RETRIES:
                raise RunStopped(entry["problem"])
            continue
        attempts.append(entry)
        if not problem:
            return {"raw": raw, "result": doc.get("result", ""), "model_ids": models,
                    "started_utc": started, "calls": attempts}
        transport_failures += 1
        if transport_failures > MAX_RETRIES:
            return {"raw": raw, "result": None, "model_ids": models, "started_utc": started,
                    "calls": attempts}


FENCE = re.compile(r"^```([^\n`]*)\n(.*?)^```", re.S | re.M)


def extract_code(text: str | None) -> str | None:
    """The first fenced block with info string `python`, else the first
    fenced block, else None."""
    if not text:
        return None
    blocks = FENCE.findall(text)
    for info, body in blocks:
        if info.strip().lower() == "python":
            return body
    return blocks[0][1] if blocks else None


def run_dir(p: Program, condition: str, attempt: int) -> Path:
    return RUNS / p.track / p.name / condition / str(attempt)


def make_call(d: Path, prompt: str, model: str, version: str) -> str | None:
    """Call (unless d already holds its artifacts) and return the extracted code."""
    record = d / "call.json"
    if record.exists():
        code_file = d / "translation.py"
        return code_file.read_text(encoding="utf-8") if code_file.exists() else None
    d.mkdir(parents=True, exist_ok=True)
    (d / "prompt.md").write_text(prompt, encoding="utf-8")
    res = call(prompt, model)
    (d / "reply.json").write_text(res["raw"], encoding="utf-8")
    code = extract_code(res["result"])
    if code is not None:
        (d / "translation.py").write_text(code, encoding="utf-8")
    meta = {"started_utc": res["started_utc"], "model_id_configured": model,
            "model_ids_reported": res["model_ids"], "client_version": version,
            "calls": res["calls"], "has_code": code is not None,
            "environment_variables": sorted(client_env("").keys())}
    record.write_text(json.dumps(meta, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return code


def first_dev_failure(p: Program, path: Path | None, condition: str):
    """(input, Verdict) of the first failing DEV vector, or None if all pass."""
    spec = p.spec()
    dev = load(p)["sets"]["dev"]
    inputs = [decode_input(v["input"]) for v in dev]
    if path is None:
        return (inputs[0] if inputs else {}), Verdict(False, "no code")
    results = run_translation(path, inputs, spec.timeout, condition)
    for inp, v, r in zip(inputs, dev, results):
        verdict = judge(spec, v["expected"][PRIMARY], r)
        if not verdict.passed:
            return inp, verdict
    return None


def run_one_shot(p: Program, condition: str, attempt: int, model: str, version: str) -> None:
    make_call(run_dir(p, condition, attempt), prompt_one_shot(p, condition), model, version)


def run_repair(p: Program, attempt: int, model: str, version: str) -> None:
    a_dir = run_dir(p, "A", attempt)
    if not (a_dir / "call.json").exists():
        raise SystemExit(f"{p.name}: condition A attempt {attempt} is missing")
    b_dir = run_dir(p, "B", attempt)
    current = a_dir / "translation.py"
    current = current if current.exists() else None
    rounds = []
    for k in range(1, REPAIR_ROUNDS + 1):
        fail = first_dev_failure(p, current, "B")
        if fail is None:
            break
        inp, verdict = fail
        rounds.append({"round": k, "dev_failure_kind": verdict.kind})
        code_text = current.read_text(encoding="utf-8") if current else ""
        d = b_dir / f"round-{k}"
        code = make_call(d, prompt_repair(p, code_text, feedback(inp, verdict)), model, version)
        if code is not None:  # a reply without code leaves the current version
            current = d / "translation.py"
    final = None if current is None else current.relative_to(ROOT).as_posix()
    b_dir.mkdir(parents=True, exist_ok=True)
    (b_dir / "final.json").write_text(json.dumps({"final": final, "rounds": rounds}, indent=1) + "\n",
                                      encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--condition", choices=["A", "B", "C"], required=True)
    ap.add_argument("--attempt", type=int, choices=[1, 2, 3], required=True)
    ap.add_argument("--track", default="E,R", help="comma-separated tracks (T: runner test only)")
    ap.add_argument("--programs", default="")
    a = ap.parse_args(argv)
    names = [n for n in a.programs.split(",") if n]
    model = configured_model()
    version = client_version()
    for track in a.track.split(","):
        for p in programs(track):
            if names and p.name not in names:
                continue
            if a.condition == "B":
                run_repair(p, a.attempt, model, version)
            else:
                run_one_shot(p, a.condition, a.attempt, model, version)
            print(f"{p.track} {p.name} {a.condition}{a.attempt} done", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

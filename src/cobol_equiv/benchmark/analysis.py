"""Measurements and failure taxonomy (docs/benchmark-protocol.md, sections
5 and 6), computed only from committed data.

    python -m cobol_equiv.benchmark.analysis failures   # write the automatic rows of failures.csv
    python -m cobol_equiv.benchmark.analysis blind      # print the blind classification list
    python -m cobol_equiv.benchmark.analysis report [--check]

`report` writes benchmark/results/summary.json and the generated blocks of
docs/benchmark.md and README.md (between the BENCHMARK markers).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
import zlib
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "benchmark" / "results"
VERDICTS = RESULTS / "verdicts.csv"
FAILURES = RESULTS / "failures.csv"
SUMMARY = RESULTS / "summary.json"
DOC = ROOT / "docs" / "benchmark.md"
README = ROOT / "README.md"
Z = 1.959964
TRACKS = ("E", "R")
CONDITIONS = ("A", "B", "C")
CATEGORIES = ["unsupported runtime feature", "crash or syntax error", "rounding", "truncation",
              "sign handling", "PICTURE editing", "string statements", "file handling",
              "loop or branch logic", "other"]
AUTOMATIC = {"unsupported": CATEGORIES[0], "error": CATEGORIES[1], "timeout": CATEGORIES[1],
             "no code": CATEGORIES[1]}
FAILURE_FIELDS = ["track", "program", "condition", "attempt", "first_failure_kind", "category",
                  "reason", "first_failure"]


# ---- statistics ----------------------------------------------------------------

def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def binom_two_sided(k: int, n: int) -> float:
    """Exact two-sided binomial test with p = 0.5 (1 when n = 0)."""
    if n == 0:
        return 1.0
    k = min(k, n - k)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def mcnemar(pairs: list[tuple[bool, bool]]) -> dict:
    b = sum(1 for x, y in pairs if x and not y)
    c = sum(1 for x, y in pairs if y and not x)
    return {"pairs": len(pairs), "first_only": b, "second_only": c, "p": binom_two_sided(b, b + c)}


def holm(ps: list[float]) -> list[float]:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj = [0.0] * len(ps)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = running
    return adj


# ---- data ----------------------------------------------------------------------

def load_verdicts() -> list[dict]:
    with VERDICTS.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def final_rows(rows: list[dict], set_name: str = "heldout", version: str = "3.1.2") -> dict:
    """(track, program, condition, attempt) -> row of the final version."""
    out = {}
    for r in rows:
        if r["set"] != set_name or r["version"] != version:
            continue
        final_round = 3 if r["condition"] == "B" else 0
        if int(r["round"]) == final_round:
            out[(r["track"], r["program"], r["condition"], int(r["attempt"]))] = r
    return out


def rate(rows: dict, track: str, condition: str) -> dict:
    sel = [r for (t, _, c, _), r in rows.items() if t == track and c == condition]
    k, n = sum(int(r["pass"]) for r in sel), len(sel)
    lo, hi = wilson(k, n)
    return {"passed": k, "attempts": n, "rate": k / n if n else None, "ci95": [lo, hi]}


def pass_at_3(rows: dict, track: str, condition: str) -> dict:
    by_prog = defaultdict(list)
    for (t, p, c, _), r in rows.items():
        if t == track and c == condition:
            by_prog[p].append(int(r["pass"]))
    k, n = sum(1 for v in by_prog.values() if any(v)), len(by_prog)
    lo, hi = wilson(k, n)
    return {"programs_passed": k, "programs": n, "rate": k / n if n else None, "ci95": [lo, hi]}


def compute(rows: list[dict]) -> dict:
    held, vis = final_rows(rows), final_rows(rows, "visible")
    out: dict = {"by_track": {}, "tests": []}
    for t in TRACKS:
        tr: dict = {"heldout": {}, "pass_at_3": {}, "visible": {}, "b_by_round": []}
        for c in CONDITIONS:
            tr["heldout"][c] = rate(held, t, c)
            tr["pass_at_3"][c] = pass_at_3(held, t, c)
            tr["visible"][c] = rate(vis, t, c)
        for rnd in range(4):
            sel = [r for r in rows if r["track"] == t and r["condition"] == "B" and r["set"] == "heldout"
                   and r["version"] == "3.1.2" and int(r["round"]) == rnd]
            k, n = sum(int(r["pass"]) for r in sel), len(sel)
            tr["b_by_round"].append({"round": rnd, "passed": k, "attempts": n, "rate": k / n if n else None,
                                     "ci95": list(wilson(k, n))})
        out["by_track"][t] = tr
        for other in ("C", "B"):
            pairs, per_prog = [], defaultdict(lambda: [0, 0])
            for (tt, p, c, a), r in held.items():
                if tt != t or c != "A" or (t, p, other, a) not in held:
                    continue
                x, y = bool(int(r["pass"])), bool(int(held[(t, p, other, a)]["pass"]))
                pairs.append((x, y))
                per_prog[p][0] += x
                per_prog[p][1] += y
            m = mcnemar(pairs)
            diffs = [a - b for a, b in per_prog.values() if a != b]
            sign = {"programs": len(per_prog), "ties_dropped": len(per_prog) - len(diffs),
                    "a_better": sum(1 for d in diffs if d > 0), "a_worse": sum(1 for d in diffs if d < 0),
                    "p": binom_two_sided(sum(1 for d in diffs if d > 0), len(diffs))}
            p3 = mcnemar([(a > 0, b > 0) for a, b in per_prog.values()])
            out["tests"].append({"track": t, "comparison": f"A vs {other}", "mcnemar": m,
                                 "sign_test": sign, "pass_at_3_mcnemar": p3})
    adj = holm([x["mcnemar"]["p"] for x in out["tests"]])
    for x, a in zip(out["tests"], adj):
        x["mcnemar"]["p_holm"] = a
    sec = final_rows(rows, version="3.2")
    out["secondary"] = {
        "run": len(sec),
        "pass": sum(int(r["pass"]) for r in sec.values()),
        "fail_on_3_2": sorted("/".join(map(str, k)) for k, r in sec.items() if not int(r["pass"])),
        "not_run_no_3_2_outputs": sorted({k[1] for k, r in held.items() if int(r["pass"])
                                          and k not in sec}),
    }
    out["taxonomy"] = taxonomy()
    return out


# ---- failure taxonomy ----------------------------------------------------------

def failing_finals(rows: list[dict]) -> list[dict]:
    held = final_rows(rows)
    return [r for k, r in sorted(held.items()) if not int(r["pass"])]


def write_failures(rows: list[dict]) -> None:
    """Rows for every failing final attempt; the automatic categories are
    filled in, existing manual categories and reasons are kept."""
    old = {}
    if FAILURES.exists():
        with FAILURES.open(encoding="utf-8", newline="") as fh:
            old = {(r["track"], r["program"], r["condition"], r["attempt"]): r for r in csv.DictReader(fh)}
    out = []
    for r in failing_finals(rows):
        key = (r["track"], r["program"], r["condition"], r["attempt"])
        auto = AUTOMATIC.get(r["first_failure_kind"], "")
        prev = old.get(key, {})
        out.append({"track": r["track"], "program": r["program"], "condition": r["condition"],
                    "attempt": r["attempt"], "first_failure_kind": r["first_failure_kind"],
                    "category": auto or prev.get("category", ""),
                    "reason": prev.get("reason", "") if not auto else (prev.get("reason") or r["first_failure"][:120]),
                    "first_failure": r["first_failure"]})
    with FAILURES.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FAILURE_FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(out)


def blind_list(rows: list[dict]) -> list[dict]:
    """Failures that need a manual category, in random order (seed
    crc32("taxonomy")), without the condition."""
    finals = {(r["track"], r["program"], r["condition"], r["attempt"]): r for r in failing_finals(rows)}
    todo = [r for k, r in finals.items() if r["first_failure_kind"] not in AUTOMATIC]
    todo.sort(key=lambda r: (r["track"], r["program"], r["condition"], r["attempt"]))
    random.Random(zlib.crc32(b"taxonomy")).shuffle(todo)
    return [{"item": i, "id": zlib.crc32(f"{r['track']}/{r['program']}/{r['condition']}/{r['attempt']}"
                                       .encode("utf-8")),
             "program": r["program"], "translation": r["translation"], "difference": r["first_failure"]}
            for i, r in enumerate(todo, 1)]


def taxonomy() -> dict:
    if not FAILURES.exists():
        return {}
    with FAILURES.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    counts: dict = {}
    for t in TRACKS:
        for c in CONDITIONS:
            sel = [r for r in rows if r["track"] == t and r["condition"] == c]
            counts[f"{t}/{c}"] = {cat: sum(1 for r in sel if r["category"] == cat) for cat in CATEGORIES}
            counts[f"{t}/{c}"]["unclassified"] = sum(1 for r in sel if r["category"] not in CATEGORIES)
    return counts


# ---- report --------------------------------------------------------------------

def _pct(x) -> str:
    return "n/a" if x is None else f"{100 * x:.1f}%"


def _ci(ci) -> str:
    return f"{100 * ci[0]:.1f}-{100 * ci[1]:.1f}%"


def _p(p: float) -> str:
    return f"{p:.3g}"


def tables(s: dict) -> str:
    lines = ["| track | condition | HELD-OUT pass (attempts) | 95% CI | pass@3 (programs) | 95% CI | "
             "VISIBLE pass (attempts) |", "|---|---|---|---|---|---|---|"]
    for t in TRACKS:
        for c in CONDITIONS:
            h, p3, v = (s["by_track"][t][k][c] for k in ("heldout", "pass_at_3", "visible"))
            lines.append(f"| {t} | {c} | {h['passed']}/{h['attempts']} ({_pct(h['rate'])}) | {_ci(h['ci95'])} | "
                         f"{p3['programs_passed']}/{p3['programs']} ({_pct(p3['rate'])}) | {_ci(p3['ci95'])} | "
                         f"{v['passed']}/{v['attempts']} ({_pct(v['rate'])}) |")
    lines += ["", "| track | comparison | pairs | A only / other only | McNemar p | Holm p | "
                  "sign test (A better / worse, p) | pass@3 McNemar p |", "|---|---|---|---|---|---|---|---|"]
    for x in s["tests"]:
        m, sg, p3 = x["mcnemar"], x["sign_test"], x["pass_at_3_mcnemar"]
        lines.append(f"| {x['track']} | {x['comparison']} | {m['pairs']} | {m['first_only']} / {m['second_only']} | "
                     f"{_p(m['p'])} | {_p(m['p_holm'])} | {sg['a_better']} / {sg['a_worse']}, {_p(sg['p'])} | "
                     f"{_p(p3['p'])} |")
    lines += ["", "| track | B after round 0 | 1 | 2 | 3 |", "|---|---|---|---|---|"]
    for t in TRACKS:
        cells = [f"{r['passed']}/{r['attempts']} ({_pct(r['rate'])})" for r in s["by_track"][t]["b_by_round"]]
        lines.append(f"| {t} | " + " | ".join(cells) + " |")
    sec = s["secondary"]
    lines += ["", f"GnuCOBOL 3.2 re-run of the final translations that pass HELD-OUT on 3.1.2: "
                  f"{sec['pass']} of {sec['run']} pass; fail on 3.2: "
                  f"{', '.join(sec['fail_on_3_2']) or 'none'}; not run (no 3.2 outputs): "
                  f"{', '.join(sec['not_run_no_3_2_outputs']) or 'none'}."]
    if s["taxonomy"]:
        lines += ["", "| category | " + " | ".join(f"{t}/{c}" for t in TRACKS for c in CONDITIONS) + " |",
                  "|---|" + "---|" * (len(TRACKS) * len(CONDITIONS))]
        for cat in CATEGORIES + ["unclassified"]:
            lines.append(f"| {cat} | " + " | ".join(str(s["taxonomy"][f"{t}/{c}"][cat]) for t in TRACKS
                                                   for c in CONDITIONS) + " |")
    return "\n".join(lines) + "\n"


def _replace_block(text: str, block: str) -> str:
    start, end = "<!-- BENCHMARK:START -->", "<!-- BENCHMARK:END -->"
    a, b = text.index(start) + len(start), text.index(end)
    return text[:a] + "\n" + block + text[b:]


def report(check: bool) -> int:
    s = compute(load_verdicts())
    summary = json.dumps(s, indent=1, sort_keys=True) + "\n"
    block = tables(s)
    targets = {SUMMARY: summary}
    for path in (DOC, README):
        if path.exists() and "<!-- BENCHMARK:START -->" in path.read_text(encoding="utf-8"):
            targets[path] = _replace_block(path.read_text(encoding="utf-8"), block)
    bad = [p for p, t in targets.items() if not p.exists() or p.read_text(encoding="utf-8") != t]
    if check:
        for p in bad:
            print(f"{p} differs from the generated content")
        return 1 if bad else 0
    for p, t in targets.items():
        p.write_text(t, encoding="utf-8")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("command", choices=["failures", "blind", "report"])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.command == "failures":
        write_failures(load_verdicts())
        return 0
    if a.command == "blind":
        for item in blind_list(load_verdicts()):
            print(json.dumps(item, ensure_ascii=False))
        return 0
    return report(a.check)


if __name__ == "__main__":
    sys.exit(main())

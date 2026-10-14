"""Measurements and failure taxonomy (docs/benchmark-protocol.md, sections
5 and 6), computed only from committed data.

    python -m cobol_equiv.benchmark.analysis failures [--runtime corrected]  # automatic rows of failures[-corrected].csv
    python -m cobol_equiv.benchmark.analysis blind      # print the blind classification list
    python -m cobol_equiv.benchmark.analysis report [--check]

`report` writes benchmark/results/summary.json and sensitivity.json and the
generated blocks of docs/benchmark.md and README.md (between the BENCHMARK
markers: the results as registered; between the SENSITIVITY markers: the
same measurements with the CobDecimal comparison defect corrected,
deviation D14, next to them).
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
VERDICTS_CORRECTED = RESULTS / "verdicts-corrected.csv"
FAILURES_CORRECTED = RESULTS / "failures-corrected.csv"
SENSITIVITY = RESULTS / "sensitivity.json"
EQ_SITES = RESULTS / "eq-sites.csv"
COMPARISONS = RESULTS / "comparisons.csv"
DOC = ROOT / "docs" / "benchmark.md"
README = ROOT / "README.md"
Z = 1.959964
TRACKS = ("E", "R")
CONDITIONS = ("A", "B", "C")
CATEGORIES = ["unsupported runtime feature", "crash or syntax error", "time-out", "rounding", "truncation",
              "sign handling", "PICTURE editing", "string statements", "file handling",
              "loop or branch logic", "other"]
# A time-out that persists under the extended limits is its own category,
# not a crash and not a semantic failure (deviation D12).
AUTOMATIC = {"unsupported": CATEGORIES[0], "error": CATEGORIES[1], "no code": CATEGORIES[1],
             "timeout": CATEGORIES[2]}
# docs/semantic-traps.md entries that match a category (protocol, section 6)
TRAPS_LINK = "@TRAPS@"  # replaced by the path from each target file
TRAPS = {
    "rounding": ("3", "3-without-rounded-extra-decimals-are-cut-never-rounded"),
    "truncation": ("4", "4-overflow-on-size-error-keeps-the-old-value-otherwise-digits-are-lost-on-the-left"),
    "sign handling": ("6", "6-negative-zero-exists"),
    "PICTURE editing": ("10", "10-numeric-editing-is-more-than-formatting"),
}
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

def load_verdicts(path: Path = VERDICTS) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
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
    return {"passed": k, "attempts": n, "rate": k / n if n else None, "ci95": [lo, hi],
            "timeouts": sum(1 for r in sel if r["first_failure_kind"] == "timeout"),
            "slow_passes": sum(1 for r in sel if int(r["pass"]) and int(r["slow_vectors"]))}


def pass_at_3(rows: dict, track: str, condition: str) -> dict:
    by_prog = defaultdict(list)
    for (t, p, c, _), r in rows.items():
        if t == track and c == condition:
            by_prog[p].append(int(r["pass"]))
    k, n = sum(1 for v in by_prog.values() if any(v)), len(by_prog)
    lo, hi = wilson(k, n)
    return {"programs_passed": k, "programs": n, "rate": k / n if n else None, "ci95": [lo, hi]}


def compute(rows: list[dict], failures: Path = FAILURES) -> dict:
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
    out["taxonomy"] = taxonomy(failures)
    return out


# ---- failure taxonomy ----------------------------------------------------------

def failing_finals(rows: list[dict]) -> list[dict]:
    held = final_rows(rows)
    return [r for k, r in sorted(held.items()) if not int(r["pass"])]


def _failure_rows(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as fh:
        return {(r["track"], r["program"], r["condition"], r["attempt"]): r for r in csv.DictReader(fh)}


def write_failures(rows: list[dict], path: Path = FAILURES, carry: Path | None = None) -> None:
    """Rows for every failing final attempt; the automatic categories are
    filled in, existing manual categories and reasons are kept. With carry
    (failures-corrected.csv: carry=failures.csv), an attempt that fails in
    the same way as in the carry file (same first failure) takes its
    category and reason from there."""
    old = _failure_rows(path)
    if carry is not None:
        for key, r in _failure_rows(carry).items():
            old.setdefault(key, r)
    out = []
    for r in failing_finals(rows):
        key = (r["track"], r["program"], r["condition"], r["attempt"])
        auto = AUTOMATIC.get(r["first_failure_kind"], "")
        prev = old.get(key, {})
        if prev.get("first_failure", r["first_failure"]) != r["first_failure"]:
            prev = {}  # fails differently: classify again
        out.append({"track": r["track"], "program": r["program"], "condition": r["condition"],
                    "attempt": r["attempt"], "first_failure_kind": r["first_failure_kind"],
                    "category": auto or prev.get("category", ""),
                    "reason": prev.get("reason", "") if not auto else (prev.get("reason") or r["first_failure"][:120]),
                    "first_failure": r["first_failure"]})
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FAILURE_FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(out)


BLIND_KEY = RESULTS / "blind-key.csv"


def blind_list(rows: list[dict]) -> list[dict]:
    """Failures that need a manual category, in random order (seed
    crc32("taxonomy")). Each item shows the program, its COBOL source as shown
    to translators, the translation code and the difference, never the
    condition, attempt or file path (the code itself can still reveal the
    condition: only condition C has no runtime import); the mapping
    from item number to attempt is written to blind-key.csv, which is read
    only to merge the categories back."""
    finals = [r for r in failing_finals(rows) if r["first_failure_kind"] not in AUTOMATIC]
    finals.sort(key=lambda r: (r["track"], r["program"], r["condition"], r["attempt"]))
    random.Random(zlib.crc32(b"taxonomy")).shuffle(finals)
    with BLIND_KEY.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["item", "track", "program", "condition", "attempt"])
        for i, r in enumerate(finals, 1):
            w.writerow([i, r["track"], r["program"], r["condition"], r["attempt"]])
    from .programs import programs
    from .prompts import source_of

    sources = {(p.track, p.name): source_of(p) for t in ("E", "R") for p in programs(t)}
    return [{"item": i, "program": r["program"], "cobol": sources[(r["track"], r["program"])],
             "translation": (ROOT / r["translation"]).read_text(encoding="utf-8"),
             "difference": r["first_failure"]}
            for i, r in enumerate(finals, 1)]


def taxonomy(failures: Path = FAILURES) -> dict:
    if not failures.exists():
        return {}
    with failures.open(encoding="utf-8", newline="") as fh:
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
             "VISIBLE pass (attempts) | time-out (attempts) | passes needing the extended time limit "
             "(depends on machine speed) |",
             "|---|---|---|---|---|---|---|---|---|"]
    for t in TRACKS:
        for c in CONDITIONS:
            h, p3, v = (s["by_track"][t][k][c] for k in ("heldout", "pass_at_3", "visible"))
            lines.append(f"| {t} | {c} | {h['passed']}/{h['attempts']} ({_pct(h['rate'])}) | {_ci(h['ci95'])} | "
                         f"{p3['programs_passed']}/{p3['programs']} ({_pct(p3['rate'])}) | {_ci(p3['ci95'])} | "
                         f"{v['passed']}/{v['attempts']} ({_pct(v['rate'])}) | {h['timeouts']} | "
                         f"{h['slow_passes']} |")
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
    crashes = crash_messages()
    if crashes:
        lines += ["", "Crash messages (crash or syntax error, by condition):", ""]
        for (c, msg), n in crashes:
            lines.append(f"- {c}: {n} x `{msg}`")
    ex = examples()
    if ex:
        lines += ["", "One example per failure category (first attempt in program order; the full list "
                      "is benchmark/results/failures.csv):", ""]
        for cat, r in ex:
            diff = r["first_failure"].replace("|", "\\|")[:220]
            trap = TRAPS.get(cat)
            link = f" See [semantic trap {trap[0]}]({TRAPS_LINK}#{trap[1]})." if trap else ""
            lines.append(f"- **{cat}** ({r['program']}): {r['reason'] or diff}. First difference: `{diff}`.{link}")
    return "\n".join(lines) + "\n"


def crash_messages() -> list:
    if not FAILURES.exists():
        return []
    from collections import Counter

    with FAILURES.open(encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r["category"] == CATEGORIES[1]]
    c = Counter((r["condition"], r["first_failure"].split(" (")[0][:100]) for r in rows)
    return sorted(c.items(), key=lambda kv: (kv[0][0], -kv[1], kv[0][1]))


def examples() -> list:
    if not FAILURES.exists():
        return []
    with FAILURES.open(encoding="utf-8", newline="") as fh:
        rows = sorted(csv.DictReader(fh), key=lambda r: (r["track"], r["program"], r["condition"], r["attempt"]))
    out = []
    for cat in CATEGORIES:
        r = next((r for r in rows if r["category"] == cat), None)
        if r:
            out.append((cat, r))
    return out


# ---- sensitivity to the CobDecimal comparison defect (D14) ---------------------

def _category(failures: dict, key) -> str:
    r = failures.get(tuple(map(str, key)))
    return "pass" if r is None else (r["category"] or "unclassified")


def usage() -> dict:
    """Per condition (A, B): translation files, and how many of them compare
    CobDecimal values in their code (eq-sites.csv) and in their HELD-OUT run
    with the registered runtime (comparisons.csv)."""
    from .eqscan import translations

    files = defaultdict(set)
    for _, _, c, _, _, path in translations():
        files[c].add(path.relative_to(ROOT).as_posix())
    out = {}
    with EQ_SITES.open(encoding="utf-8", newline="") as fh:
        sites = list(csv.DictReader(fh))
    with COMPARISONS.open(encoding="utf-8", newline="") as fh:
        runs = [r for r in csv.DictReader(fh) if r["translation"]]
    for c in ("A", "B"):
        own = files[c]  # B: the repair-round translations (round 0 of B is the A translation)
        st = {k: sorted({r["translation"] for r in sites if r["condition"] == c and r["kind"] == k})
              for k in ("eq", "order", "in", "hash")}
        dyn_rows = [r for r in runs if r["translation"] in own]
        dyn = {k: sorted({r["translation"] for r in dyn_rows if int(r[k])})
               for k in ("eq", "eq_diff", "order", "hash")}
        out[c] = {"files": len(own),
                  "static": {k: len(v) for k, v in st.items()},
                  "static_sites": {k: sum(1 for r in sites if r["condition"] == c and r["kind"] == k)
                                   for k in st},
                  "dynamic": {k: len(v) for k, v in dyn.items()},
                  "static_eq_files": st["eq"], "dynamic_eq_diff_files": dyn["eq_diff"]}
    return out


def sensitivity() -> dict:
    reg_rows, cor_rows = load_verdicts(VERDICTS), load_verdicts(VERDICTS_CORRECTED)
    reg, cor = compute(reg_rows), compute(cor_rows, FAILURES_CORRECTED)
    reg_f, cor_f = _failure_rows(FAILURES), _failure_rows(FAILURES_CORRECTED)
    a, b = final_rows(reg_rows), final_rows(cor_rows)
    flips = []
    for key in sorted(set(a) | set(b)):
        before, after = _category(reg_f, key), _category(cor_f, key)
        pa, pb = int(a[key]["pass"]), int(b[key]["pass"])
        if pa != pb or before != after:
            flips.append({"track": key[0], "program": key[1], "condition": key[2], "attempt": key[3],
                          "registered": before, "corrected": after,
                          "corrected_first_failure": b[key]["first_failure"][:200]})
    def held(rows):
        keys = ("track", "program", "condition", "attempt", "round")
        return {tuple(r[k] for k in keys): r["pass"] for r in rows
                if r["set"] == "heldout" and r["version"] == "3.1.2"}

    ha, hb = held(reg_rows), held(cor_rows)
    rounds = ["/".join(k) for k in sorted(set(ha) | set(hb)) if ha.get(k) != hb.get(k)]
    return {"registered": reg, "corrected": cor, "flips": flips, "flipped_rows_heldout_3_1_2": rounds,
            "usage": usage()}


def sensitivity_tables(x: dict) -> str:
    reg, cor = x["registered"], x["corrected"]
    lines = ["| track | condition | HELD-OUT pass, as registered | 95% CI | HELD-OUT pass, defect corrected | "
             "95% CI | pass@3, as registered | pass@3, corrected |", "|---|---|---|---|---|---|---|---|"]
    for t in TRACKS:
        for c in CONDITIONS:
            h, h2 = reg["by_track"][t]["heldout"][c], cor["by_track"][t]["heldout"][c]
            p, p2 = reg["by_track"][t]["pass_at_3"][c], cor["by_track"][t]["pass_at_3"][c]
            lines.append(f"| {t} | {c} | {h['passed']}/{h['attempts']} ({_pct(h['rate'])}) | {_ci(h['ci95'])} | "
                         f"{h2['passed']}/{h2['attempts']} ({_pct(h2['rate'])}) | {_ci(h2['ci95'])} | "
                         f"{p['programs_passed']}/{p['programs']} | {p2['programs_passed']}/{p2['programs']} |")
    lines += ["", "| track | comparison | A only / other only, as registered | McNemar p | Holm p | "
                  "A only / other only, corrected | McNemar p | Holm p | sign test p, as registered / corrected |",
              "|---|---|---|---|---|---|---|---|---|"]
    for r, k in zip(reg["tests"], cor["tests"]):
        m, m2 = r["mcnemar"], k["mcnemar"]
        lines.append(f"| {r['track']} | {r['comparison']} | {m['first_only']} / {m['second_only']} | {_p(m['p'])} | "
                     f"{_p(m['p_holm'])} | {m2['first_only']} / {m2['second_only']} | {_p(m2['p'])} | "
                     f"{_p(m2['p_holm'])} | {_p(r['sign_test']['p'])} / {_p(k['sign_test']['p'])} |")
    lines += ["", "| track | B after round 0, as registered / corrected | 1 | 2 | 3 |", "|---|---|---|---|---|"]
    for t in TRACKS:
        cells = [f"{r['passed']}/{r['attempts']} / {k['passed']}/{k['attempts']}"
                 for r, k in zip(reg["by_track"][t]["b_by_round"], cor["by_track"][t]["b_by_round"])]
        lines.append(f"| {t} | " + " | ".join(cells) + " |")
    u = x["usage"]
    lines += ["", "| condition | translation files | with == / != on CobDecimal in the code | "
                  "whose HELD-OUT run made an == / != call the defect answers differently | "
                  "with an ordering of CobDecimal in the code | in / set / dict / hash in the code |",
              "|---|---|---|---|---|---|"]
    for c in ("A", "B"):
        v = u[c]
        lines.append(f"| {c} | {v['files']} | {v['static']['eq']} ({v['static_sites']['eq']} sites) | "
                     f"{v['dynamic']['eq_diff']} | {v['static']['order']} | "
                     f"{v['static']['in'] + v['static']['hash']} |")
    lines += ["", f"Final attempts whose HELD-OUT verdict or failure category changes ({len(x['flips'])}; "
                  "category \"pass\" means the attempt passes):", ""]
    if x["flips"]:
        lines += ["| track | program | condition | attempt | as registered | defect corrected |",
                  "|---|---|---|---|---|---|"]
        for f in x["flips"]:
            lines.append(f"| {f['track']} | {f['program']} | {f['condition']} | {f['attempt']} | "
                         f"{f['registered']} | {f['corrected']} |")
    else:
        lines.append("none")
    sec = cor["secondary"]
    lines += ["", f"Defect corrected, GnuCOBOL 3.2 re-run of the final translations that pass HELD-OUT on 3.1.2: "
                  f"{sec['pass']} of {sec['run']} pass; fail on 3.2: {', '.join(sec['fail_on_3_2']) or 'none'}."]
    return "\n".join(lines) + "\n"


BLOCKS = ("BENCHMARK", "SENSITIVITY")


def _replace_block(text: str, block: str, name: str = "BENCHMARK") -> str:
    start, end = f"<!-- {name}:START -->", f"<!-- {name}:END -->"
    a, b = text.index(start) + len(start), text.index(end)
    return text[:a] + "\n" + block + text[b:]


def report(check: bool) -> int:
    s = compute(load_verdicts())
    summary = json.dumps(s, indent=1, sort_keys=True) + "\n"  # no links in the JSON
    x = sensitivity()
    blocks = {"BENCHMARK": tables(s), "SENSITIVITY": sensitivity_tables(x)}
    targets = {SUMMARY: summary, SENSITIVITY: json.dumps(x, indent=1, sort_keys=True) + "\n"}
    missing = []
    for path in (DOC, README):
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        rel = "semantic-traps.md" if path == DOC else "docs/semantic-traps.md"
        for name in BLOCKS:
            if f"<!-- {name}:START -->" in text and f"<!-- {name}:END -->" in text:
                text = _replace_block(text, blocks[name].replace(TRAPS_LINK, rel), name)
            else:
                missing.append((path, name))
        targets[path] = text
    if missing:
        for p, name in missing:
            print(f"{p} has no {name}:START/END block")
        return 1
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
    ap.add_argument("--runtime", choices=["registered", "corrected"], default="registered")
    a = ap.parse_args(argv)
    if a.command == "failures":
        if a.runtime == "corrected":
            write_failures(load_verdicts(VERDICTS_CORRECTED), FAILURES_CORRECTED, carry=FAILURES)
        else:
            write_failures(load_verdicts())
        return 0
    if a.command == "blind":
        for item in blind_list(load_verdicts()):
            print(json.dumps(item, ensure_ascii=False))
        return 0
    return report(a.check)


if __name__ == "__main__":
    sys.exit(main())

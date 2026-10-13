"""Generate results/SUMMARY.md and the derived CSV files from the committed
per-compiler results.

    python -m cobol_equiv.report [--results results] [--readme README.md]

Layout: results/gnucobol-<version>/{environment,oracle_cases,corpus,mutation}.csv
for every compiler version that was run. This module only reads those files
and derives from them:

    results/version_diff.csv            oracle cases where the GnuCOBOL output
                                        differs between versions
    results/unsupported_categories.csv  refused oracle cases by category

Only numbers present in the CSV files are reported.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, OrderedDict
from pathlib import Path

OUTCOMES = ("agree", "disagree", "unsupported", "gnucobol-crash")

# Unsupported reasons, as raised by the runtime, grouped into categories.
UNSUPPORTED_CATEGORIES = [
    ("binary-ge-2^63", r"store of a value >= 2\*\*63 into binary item",
     "value of 2**63 or more stored into a binary item without ON SIZE ERROR"),
    ("edit-fixed-plus-floating", r"PICTURE .*fixed leading sign or currency symbol combined",
     "edited picture combining a fixed sign or $ with a floating string"),
    ("single-op-comp5-negative", r"single-operand ADD/SUBTRACT giving a negative value in unsigned COMP-5",
     "single-operand ADD/SUBTRACT, negative result in an unsigned COMP-5 item"),
    ("single-op-comp3-even-overflow", r"single-operand ADD/SUBTRACT overflowing even-digit COMP-3",
     "single-operand ADD/SUBTRACT, overflow of a COMP-3 item with an even digit count"),
    ("literal-too-long", r"numeric literal .* does not fit",
     "numeric literal with more integer digits than the receiver"),
]


def unsupported_category(message: str) -> str:
    for key, pattern, _ in UNSUPPORTED_CATEGORIES:
        if re.search(pattern, message):
            return key
    return "other: " + message[:60]


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _write(path: Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def _table(header: list[str], rows: list[list]) -> list[str]:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return out


def versions(results: Path) -> list[str]:
    def key(v):
        return [int(x) for x in v.split(".")]
    return sorted((p.name.split("-", 1)[1] for p in results.glob("gnucobol-*") if p.is_dir()), key=key)


def vdir(results: Path, v: str) -> Path:
    return results / f"gnucobol-{v}"


# ---- derived data ------------------------------------------------------------

def version_diff_rows(results: Path) -> list[list]:
    vs = versions(results)
    if len(vs) < 2:
        return []
    data = {v: {r["case"]: r for r in _read(vdir(results, v) / "oracle_cases.csv")} for v in vs}
    base = data[vs[0]]
    rows = []
    for case, r in base.items():
        outs = [data[v].get(case, {}).get("gnucobol", "") for v in vs]
        if len(set(outs)) > 1:
            rows.append([r["rule"], case, r["params"]] + [o[7:] for o in outs]
                        + [data[v].get(case, {}).get("outcome", "") for v in vs])
    return rows


def unsupported_rows(results: Path) -> list[list]:
    vs = versions(results)
    counts = {v: Counter() for v in vs}
    for v in vs:
        for r in _read(vdir(results, v) / "oracle_cases.csv"):
            if r["outcome"] == "unsupported":
                counts[v][unsupported_category(r["python"].split("UNSUPPORTED ", 1)[1])] += 1
    keys = [k for k, _, _ in UNSUPPORTED_CATEGORIES]
    keys += sorted({k for c in counts.values() for k in c} - set(keys))
    desc = {k: d for k, _, d in UNSUPPORTED_CATEGORIES}
    rows = [[k, desc.get(k, k)] + [counts[v][k] for v in vs] for k in keys]
    rows = [r for r in rows if any(r[2:])]
    rows.append(["total", ""] + [sum(counts[v].values()) for v in vs])
    return rows


# ---- sections ------------------------------------------------------------------

def oracle_section(results: Path) -> list[str]:
    vs = versions(results)
    per = {v: _read(vdir(results, v) / "oracle_cases.csv") for v in vs}
    rules: "OrderedDict[str, dict]" = OrderedDict()
    for v in vs:
        for r in per[v]:
            rules.setdefault(r["rule"], {w: Counter() for w in vs})[v][r["outcome"]] += 1
    header = ["rule", "cases"] + [f"{v}: agree / disagree / unsupported / crash" for v in vs]
    table, tot = [], {v: Counter() for v in vs}
    for rule, c in rules.items():
        n = sum(c[vs[0]].values())
        row = [rule, n]
        for v in vs:
            tot[v].update(c[v])
            row.append(" / ".join(str(c[v][o]) for o in OUTCOMES))
        table.append(row)
    table.append(["**total**", sum(tot[vs[0]].values())]
                 + [" / ".join(str(tot[v][o]) for o in OUTCOMES) for v in vs])
    out = ["## Runtime vs GnuCOBOL (oracle)", "",
           "Source: `results/gnucobol-<version>/oracle_cases.csv`, produced by "
           "`python -m cobol_equiv.oracle.run` with each compiler. The runtime models GnuCOBOL "
           "3.1.2; disagreements with other versions are expected where their behaviour "
           "differs. `unsupported`: the runtime refused the case (see below). `crash`: the "
           "GnuCOBOL program for that case did not exit normally even when run alone.", ""]
    out += _table(header, table)
    urows = unsupported_rows(results)
    if urows:
        out += ["", "Refused (unsupported) cases by category "
                    "(`results/unsupported_categories.csv`):", ""]
        out += _table(["category", "description"] + vs, urows)
    for v in vs:
        aborts = _read(vdir(results, v) / "oracle_aborts.csv")
        if aborts:
            out += ["", f"GnuCOBOL {v}: {len(aborts)} oracle program(s) did not exit normally "
                        "(`oracle_aborts.csv`); their cases were run again one by one, and the "
                        "results above come from those single-case runs. First message: "
                        f"\"{aborts[0]['stderr']}\"."]
    for v in vs:
        bad = [r for r in per[v] if r["outcome"] in ("disagree", "gnucobol-crash")]
        if bad:
            by = Counter(r["rule"] for r in bad)
            out += ["", f"Disagreements with GnuCOBOL {v}, by rule: "
                    + ", ".join(f"{k} {n}" for k, n in by.items()) + "."]
    return out + [""]


def version_section(results: Path) -> list[str]:
    vs = versions(results)
    rows = version_diff_rows(results)
    if len(vs) < 2:
        return []
    by_rule = Counter(r[0] for r in rows)
    total = Counter(r["rule"] for r in _read(vdir(results, vs[0]) / "oracle_cases.csv"))
    out = [f"## GnuCOBOL {' vs '.join(vs)}", "",
           "Oracle cases whose GnuCOBOL output differs between the versions "
           "(`results/version_diff.csv` lists every case).", ""]
    out += _table(["rule", "cases", "output differs"],
                  [[k, total[k], n] for k, n in sorted(by_rule.items())]
                  + [["**total**", sum(total.values()), len(rows)]])
    return out + [""]


def corpus_section(results: Path) -> list[str]:
    vs = versions(results)
    per = {v: {r["program"]: r for r in _read(vdir(results, v) / "corpus.csv")} for v in vs}
    progs = sorted({p for v in vs for p in per[v]})
    if not progs:
        return []
    header = ["program", "semantic area"] + [f"GnuCOBOL {v}" for v in vs]
    rows = []
    for p in progs:
        r0 = next(per[v][p] for v in vs if p in per[v])
        rows.append([p, r0["area"]] + [
            (f"{per[v][p]['result']} (vectors {per[v][p]['vectors']}, generated "
             f"{per[v][p]['generated']}; boundary {per[v][p]['boundary result']}, "
             f"{per[v][p]['boundary vectors']} vectors)") if p in per[v] else "-" for v in vs])
    out = ["## Corpus: reference translations vs GnuCOBOL", "",
           "Source: `results/gnucobol-<version>/corpus.csv`. The reference translations were "
           "written against GnuCOBOL 3.1.2.", ""]
    out += _table(header, rows)
    for v in vs:
        for p in progs:
            if p in per[v] and per[v][p]["result"] != "pass":
                out += ["", f"{p} on GnuCOBOL {v}: {per[v][p]['difference']}"]
            if p in per[v] and per[v][p]["boundary result"] != "pass":
                out += ["", f"{p} on GnuCOBOL {v}, boundary vectors: "
                        f"{per[v][p]['boundary difference']}"]
    return out + [""]


def mutation_counts(rows: list[dict]) -> Counter:
    """(a) fixed vectors + generated inputs; (b) the same plus the boundary
    vectors. A mutant labelled equivalent is not counted as missed."""
    c = Counter()
    for r in rows:
        eq = r["equivalence"] == "claimed"
        c["mutants"] += 1
        c["equivalent"] += eq
        c["disproved"] += r["equivalence"] == "disproved"
        for col, key in (("status", "a"), ("status_with_boundary", "b")):
            if r[col] == "killed":
                c[f"killed {key}"] += 1
            elif not eq:
                c[f"missed {key}"] += 1
    return c


MUTATION_COLS = ["mutants", "equivalent", "killed a", "missed a", "killed b", "missed b"]


def mutation_section(results: Path) -> list[str]:
    vs = [v for v in versions(results) if _read(vdir(results, v) / "mutation.csv")]
    if not vs:
        return []
    v = vs[0]
    rows = _read(vdir(results, v) / "mutation.csv")
    by_cat: "OrderedDict[str, list]" = OrderedDict()
    for r in rows:
        by_cat.setdefault(r["category"], []).append(r)
    table = [[cat] + [mutation_counts(rs)[k] for k in MUTATION_COLS] for cat, rs in by_cat.items()]
    tot = mutation_counts(rows)
    table.append(["**total**"] + [tot[k] for k in MUTATION_COLS])
    out = ["## Mutation testing of the harness", "",
           f"Source: `results/gnucobol-{v}/mutation.csv`. A mutant is a deliberately wrong copy "
           "of a reference translation; it is killed when the harness reports a difference "
           "against GnuCOBOL. Two measurements: (a) the fixed regression vectors and the "
           "generated inputs; (b) the same plus the boundary vectors derived from the PICTURE "
           "clauses only (`harness/boundary.py`). `equivalent`: labelled as unable to change the "
           "output, with the argument or exhaustive check in `docs/mutants.md`; not counted as "
           "missed. `missed`: survived and not labelled equivalent.", ""]
    out += _table(["category", "mutants", "equivalent", "killed (a)", "missed (a)", "killed (b)",
                   "missed (b)"], table)
    if tot["disproved"]:
        out += ["", f"Equivalence labels contradicted by a kill: {tot['disproved']}."]
    surv = [r for r in rows if r["status"] == "survived"]
    if surv:
        out += ["", "Mutants that survived (a):", ""]
        out += _table(["program", "mutant", "kind", "(b)", "why it survived"],
                      [[r["program"], r["mutant"], r["survivor_kind"],
                        (f"killed by {r['detected_by_with_boundary']}"
                         if r["status_with_boundary"] == "killed" else "survived"),
                        r["note"] or "(not analysed)"] for r in surv])
    return out + [""]


# ---- README block ----------------------------------------------------------------

START = "<!-- results:start (generated by python -m cobol_equiv.report, do not edit) -->"
END = "<!-- results:end -->"


def readme_block(results: Path) -> str:
    rows = []
    for v in versions(results):
        d = vdir(results, v)
        env = {r["key"]: r["value"] for r in _read(d / "environment.csv")}
        oracle = _read(d / "oracle_cases.csv")
        oc = Counter(r["outcome"] for r in oracle)
        corpus = _read(d / "corpus.csv")
        aborts = len(_read(d / "oracle_aborts.csv"))
        rows.append([f"GnuCOBOL {v}", "oracle",
                     f"{len(oracle)} generated cases in {len({r['rule'] for r in oracle})} rules: "
                     f"{oc['agree']} agree, {oc['disagree']} disagree, {oc['unsupported']} refused "
                     f"as unsupported, {oc['gnucobol-crash']} single-case GnuCOBOL crashes; "
                     f"{aborts} multi-case oracle programs aborted (their cases were rerun alone)"])
        rows.append([f"GnuCOBOL {v}", "corpus",
                     f"{sum(r['result'] == 'pass' for r in corpus)} of {len(corpus)} reference "
                     f"translations pass (regression vectors plus up to "
                     f"{env.get('generated inputs per program and mutant (max)', '?')} generated inputs); "
                     f"{sum(r.get('boundary result') == 'pass' for r in corpus)} of {len(corpus)} "
                     f"pass the PICTURE boundary vectors"])
        mut = _read(d / "mutation.csv")
        if mut:
            c = mutation_counts(mut)
            rows.append([f"GnuCOBOL {v}", "mutation",
                         f"{c['mutants']} mutants, {c['equivalent']} labelled equivalent "
                         f"(docs/mutants.md); fixed and generated inputs: {c['killed a']} killed, "
                         f"{c['missed a']} missed; plus PICTURE boundary vectors: "
                         f"{c['killed b']} killed, {c['missed b']} missed"])
    diff = version_diff_rows(results)
    if diff:
        vs = versions(results)
        rows.append([f"{vs[0]} vs {vs[-1]}", "oracle",
                     f"GnuCOBOL output differs in {len(diff)} cases "
                     f"({', '.join(f'{k} {n}' for k, n in Counter(r[0] for r in diff).items())})"])
    lines = [START, ""] + _table(["compiler", "what", "result"], rows) + [
        "", "Details: [results/SUMMARY.md](results/SUMMARY.md).", "", END]
    return "\n".join(lines)


def update_readme(readme: Path, results: Path) -> None:
    text = readme.read_text(encoding="utf-8")
    a, b = text.index(START), text.index(END) + len(END)
    readme.write_text(text[:a] + readme_block(results) + text[b:], encoding="utf-8")


def build(results: Path) -> str:
    lines = ["# Results summary", "",
             "Generated by `python -m cobol_equiv.report` from the CSV files in this directory. "
             "Do not edit by hand.", ""]
    for v in versions(results):
        env = _read(vdir(results, v) / "environment.csv")
        if env:
            lines += [f"Environment for GnuCOBOL {v}:", ""]
            lines += _table(["key", "value"], [[r["key"], r["value"]] for r in env]) + [""]
    lines += oracle_section(results)
    lines += version_section(results)
    lines += corpus_section(results)
    lines += mutation_section(results)
    return "\n".join(lines).rstrip("\n") + "\n"


def write_derived(results: Path) -> None:
    vs = versions(results)
    if len(vs) >= 2:
        _write(results / "version_diff.csv",
               ["rule", "case", "params"] + [f"gnucobol {v}" for v in vs] + [f"outcome {v}" for v in vs],
               version_diff_rows(results))
    _write(results / "unsupported_categories.csv", ["category", "description"] + vs,
           unsupported_rows(results))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--readme", default="README.md", help="README with a results block to refresh")
    a = ap.parse_args(argv)
    res = Path(a.results)
    write_derived(res)
    (res / "SUMMARY.md").write_text(build(res), encoding="utf-8")
    if a.readme and Path(a.readme).exists():
        update_readme(Path(a.readme), res)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

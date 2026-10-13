"""Run oracle cases through GnuCOBOL and the Python runtime and compare.

    python -m cobol_equiv.oracle.run [--out results] [--rules a,b]

Writes <out>/oracle_cases.csv (one row per case) and returns the rows.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import hashlib
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ..cobc import COBC_FLAGS, clean_env, cobc_path, cobc_version
from ..runtime.display import display_bytes
from ..runtime.errors import Unsupported
from ..runtime.storage import Group, Item, Storage
from .cobolgen import AREA_A, AREA_B, data_decl, program, stmt
from .rules import RULES, Case, all_cases

CHUNK = 200
BUILD_DIR = Path(".cobol-build") / "oracle"

HEX_DATA = [
    f"{AREA_A}01 HEX-IN PIC X(200).",
    f"{AREA_A}01 HEX-OUT PIC X(400).",
    f"{AREA_A}01 HEX-LEN PIC 9(4).",
    f"{AREA_A}01 HEX-I PIC 9(4).",
    f"{AREA_A}01 HEX-V PIC 9(4).",
    f"{AREA_A}01 HEX-H PIC 9(4).",
    f"{AREA_A}01 HEX-L PIC 9(4).",
    f'{AREA_A}01 HEX-DIGITS PIC X(16) VALUE "0123456789ABCDEF".',
]
HEX_PARA = [
    f"{AREA_A}HEX-DUMP.",
    f"{AREA_B}MOVE SPACES TO HEX-OUT",
    f"{AREA_B}PERFORM VARYING HEX-I FROM 1 BY 1 UNTIL HEX-I > HEX-LEN",
    f"{AREA_B}  COMPUTE HEX-V = FUNCTION ORD(HEX-IN(HEX-I:1)) - 1",
    f"{AREA_B}  DIVIDE HEX-V BY 16 GIVING HEX-H REMAINDER HEX-L",
    f"{AREA_B}  MOVE HEX-DIGITS(HEX-H + 1:1) TO HEX-OUT(2 * HEX-I - 1:1)",
    f"{AREA_B}  MOVE HEX-DIGITS(HEX-L + 1:1) TO HEX-OUT(2 * HEX-I:1)",
    f"{AREA_B}END-PERFORM",
    f"{AREA_B}DISPLAY HEX-OUT(1:2 * HEX-LEN) WITH NO ADVANCING.",
]


def _rename(item: Item, prefix: str) -> Item:
    return dataclasses.replace(
        item, name=f"{prefix}-{item.name}",
        redefines=f"{prefix}-{item.redefines}" if item.redefines else None,
        children=[_rename(c, prefix) for c in item.children])


def _sub(text: str, names: dict[str, str]) -> str:
    for k, v in names.items():
        text = text.replace("{" + k + "}", v)
    return text


def case_tag(i: int) -> str:
    return f"C{i:05d}"


def cobol_for_chunk(name: str, chunk: list[tuple[int, Case]]) -> str:
    data = list(HEX_DATA)
    proc = [f"{AREA_A}MAIN-PARA."]
    for i, c in chunk:
        tag = case_tag(i)
        names = {it.name: f"{tag}-{it.name}" for it in c.items}
        for it in c.items:
            data += data_decl(_rename(it, tag))
        proc += stmt(f'DISPLAY "{tag}" WITH NO ADVANCING')
        proc += stmt('MOVE "N" TO SE-FLAG')
        for s in c.cobol:
            proc += stmt(_sub(s, names))
        for kind, x in c.out:
            if kind == "flag":
                proc += stmt('DISPLAY " " SE-FLAG WITH NO ADVANCING')
            elif kind == "hex":
                proc += stmt('DISPLAY " " WITH NO ADVANCING')
                proc += stmt(f"MOVE G-{names[x]} TO HEX-IN")
                proc += stmt(f"MOVE LENGTH OF G-{names[x]} TO HEX-LEN")
                proc += stmt("PERFORM HEX-DUMP")
            elif kind == "disp":
                proc += stmt(f'DISPLAY " " {names[x]} WITH NO ADVANCING')
            elif kind == "len":
                proc += stmt(f"MOVE LENGTH OF {names[x]} TO LEN-OUT")
                proc += stmt('DISPLAY " " LEN-OUT WITH NO ADVANCING')
        proc += stmt('DISPLAY "|"')
    proc += [f"{AREA_B}STOP RUN."] + HEX_PARA
    return program(name, data, proc)


def python_line(i: int, c: Case) -> str:
    try:
        st = Storage("CASE", [Group(f"G-{it.name}", [it]) for it in c.items])
        f = {it.name: st[it.name] for it in c.items}
        f["_storage"] = st
        err = c.py(f)
        parts = [case_tag(i)]
        for kind, x in c.out:
            if kind == "flag":
                parts.append("Y" if err else "N")
            elif kind == "hex":
                parts.append(f[x].raw.hex().upper())
            elif kind == "disp":
                parts.append(display_bytes(f[x]).decode("latin-1"))
            elif kind == "len":
                parts.append(str(f[x].size).zfill(6))
        return " ".join(parts) + "|"
    except Unsupported as e:  # outside the documented subset: reported separately
        return f"{case_tag(i)} UNSUPPORTED {e}"
    except Exception as e:  # recorded as a disagreement, not hidden
        return f"{case_tag(i)} PYTHON-ERROR {type(e).__name__}: {e}"


def run_chunk(name: str, chunk, build: Path) -> dict[int, str]:
    src = cobol_for_chunk(name, chunk)
    key = cobc_version() + "\0" + " ".join(COBC_FLAGS) + "\0" + src
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    cob = build / f"{name}-{digest}.cob"
    exe = build / f"{name}-{digest}"
    if not exe.exists():
        cob.write_text(src, encoding="utf-8")
        r = subprocess.run([cobc_path(), *COBC_FLAGS, "-o", str(exe), str(cob)],
                           capture_output=True, env=clean_env())
        if r.returncode != 0:
            err = r.stderr.decode("utf-8", "replace")
            errs = [ln for ln in err.splitlines() if "error" in ln][:5]
            return {i: f"{case_tag(i)} COMPILE-ERROR {' / '.join(errs)}" for i, _ in chunk}
    r = subprocess.run([str(exe)], capture_output=True, env=clean_env(), timeout=120)
    out: dict[int, str] = {}
    for line in r.stdout.decode("latin-1").split("\n"):
        if line.startswith("C") and line[1:6].isdigit():
            out[int(line[1:6])] = line
    for i, _ in chunk:
        out.setdefault(i, f"{case_tag(i)} NO-OUTPUT rc={r.returncode} "
                          f"{r.stderr.decode('latin-1', 'replace').strip()[:200]}")
    return out


def run(rules: list[str] | None = None, build: Path = BUILD_DIR, jobs: int = 4) -> list[dict]:
    if cobc_path() is None:
        raise SystemExit("cobc not found")
    cases = all_cases()
    indexed = [(i, c) for i, c in enumerate(cases) if rules is None or
               c.rule in rules or any(c.rule.startswith(r) for r in rules)]
    build.mkdir(parents=True, exist_ok=True)
    chunks = [indexed[k:k + CHUNK] for k in range(0, len(indexed), CHUNK)]
    cobol_out: dict[int, str] = {}
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        futs = [ex.submit(run_chunk, f"ORC{n:03d}", ch, build) for n, ch in enumerate(chunks)]
        for fu in futs:
            cobol_out.update(fu.result())
    rows = []
    for i, c in indexed:
        exp = cobol_out[i]
        act = python_line(i, c)
        if exp == act:
            outcome = "agree"
        elif act.startswith(f"{case_tag(i)} UNSUPPORTED"):
            outcome = "unsupported"
        else:
            outcome = "disagree"
        rows.append({"rule": c.rule, "case": case_tag(i), "params": c.params,
                     "gnucobol": exp, "python": act, "outcome": outcome})
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["rule", "case", "params", "gnucobol", "python", "outcome"])
        w.writeheader()
        w.writerows(rows)


def write_environment(out: Path) -> None:
    import platform

    from .rules import SEED

    rows = [("cobc", cobc_version()), ("cobc flags", " ".join(COBC_FLAGS)),
            ("platform", f"{platform.system()} {platform.machine()}"),
            ("oracle seed", str(SEED))]
    out.mkdir(parents=True, exist_ok=True)
    with (out / "environment.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["key", "value"])
        w.writerows(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results")
    ap.add_argument("--rules", default="")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args(argv)
    rows = run([r for r in a.rules.split(",") if r] or None, jobs=a.jobs)
    write_csv(rows, Path(a.out) / "oracle_cases.csv")
    write_environment(Path(a.out))
    bad = [r for r in rows if r["outcome"] == "disagree"]
    uns = [r for r in rows if r["outcome"] == "unsupported"]
    print(f"{len(rows)} cases, {len(rows) - len(bad) - len(uns)} agree, "
          f"{len(bad)} disagree, {len(uns)} unsupported")
    for r in bad[:20]:
        print(f"  {r['rule']} {r['params']}\n    gnucobol: {r['gnucobol']}\n    python:   {r['python']}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())

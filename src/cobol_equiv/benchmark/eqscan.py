"""Static scan of the committed translations for comparisons of CobDecimal
values (deviation D14).

    python -m cobol_equiv.benchmark.eqscan [--check]

Writes benchmark/results/eq-sites.csv: one row per site in a condition A or
B translation (B: the translation of each repair round) where a CobDecimal
value is compared with == or != ("eq"), ordered with <, <=, >, >= or by
min, max or sorted ("order"), tested with in / not in ("in"), or used as a
set element, a dict key or an argument of hash() ("hash").

A value counts as a CobDecimal when it is a call of dec, CobDecimal,
CobDecimal.of or .to_cobdec() (also under an import alias), an arithmetic
expression with such an operand, a name assigned such a value anywhere in
the same function (or at module level), or a call of a function of the
module that returns one. The scan is approximate: values passed through
containers, attributes or parameters are not followed. The driver's
dynamic counts (verify, comparisons.csv) are the complement: they count the
calls actually made on the HELD-OUT vectors.
"""

from __future__ import annotations

import argparse
import ast
import csv
import io
import sys
from pathlib import Path

from .programs import programs

ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "benchmark" / "runs"
OUT = ROOT / "benchmark" / "results" / "eq-sites.csv"
FIELDS = ["track", "program", "condition", "attempt", "round", "line", "kind", "code", "translation"]
CONSTRUCTORS = {"dec", "CobDecimal"}
ORDERING_CALLS = {"min", "max", "sorted"}


def translations() -> list[tuple[str, str, str, int, int, Path]]:
    """(track, program, condition, attempt, round, path) of every A and B translation file."""
    out = []
    for track in ("E", "R"):
        for p in programs(track):
            base = RUNS / track / p.name
            for attempt in (1, 2, 3):
                a = base / "A" / str(attempt) / "translation.py"
                if a.exists():
                    out.append((track, p.name, "A", attempt, 0, a))
                for r in sorted((base / "B" / str(attempt)).glob("round-*/translation.py")):
                    out.append((track, p.name, "B", attempt, int(r.parent.name.split("-")[1]), r))
    return out


class _Scan:
    def __init__(self, tree: ast.Module):
        self.tree = tree
        self.ctor = set(CONSTRUCTORS)  # local names of dec / CobDecimal
        self.modules = set()  # local names of the runtime package or module
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("cobol_equiv"):
                for a in node.names:
                    if a.name in CONSTRUCTORS:
                        self.ctor.add(a.asname or a.name)
                    elif a.name in ("runtime", "cobdec"):
                        self.modules.add(a.asname or a.name)
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.startswith("cobol_equiv"):
                        self.modules.add(a.asname or a.name.split(".")[0])
        self.functions = {n.name: n for n in ast.walk(tree)
                          if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.returns_dec: set[str] = set()
        self.dec_names: dict[ast.AST, set[str]] = {}
        for _ in range(5):  # names and functions depend on each other: iterate to a fixed point
            before = (set(self.returns_dec), {k: set(v) for k, v in self.dec_names.items()})
            for scope in [tree, *self.functions.values()]:
                self.dec_names[scope] = self._assigned(scope)
            for name, f in self.functions.items():
                if any(isinstance(n, ast.Return) and n.value is not None and self.is_dec(n.value, f)
                       for n in self._own(f)):
                    self.returns_dec.add(name)
            if before == (self.returns_dec, self.dec_names):
                break

    @staticmethod
    def _own(scope):
        """The nodes of a scope, without those of nested functions."""
        stack = list(ast.iter_child_nodes(scope))
        while stack:
            n = stack.pop()
            yield n
            if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                stack.extend(ast.iter_child_nodes(n))

    def _assigned(self, scope) -> set[str]:
        names = set(self.dec_names.get(scope, set()))
        for n in self._own(scope):
            if isinstance(n, ast.Assign) and self.is_dec(n.value, scope):
                for t in n.targets:
                    if isinstance(t, ast.Name):
                        names.add(t.id)
            elif isinstance(n, (ast.AnnAssign, ast.AugAssign)) and n.value is not None \
                    and isinstance(n.target, ast.Name) and self.is_dec(n.value, scope):
                names.add(n.target.id)
            elif isinstance(n, ast.NamedExpr) and self.is_dec(n.value, scope):
                names.add(n.target.id)
        return names

    def is_dec(self, e: ast.AST, scope) -> bool:
        if isinstance(e, ast.Call):
            f = e.func
            if isinstance(f, ast.Name):
                return f.id in self.ctor or f.id in self.returns_dec
            if isinstance(f, ast.Attribute):
                if f.attr == "to_cobdec":
                    return True
                if f.attr in CONSTRUCTORS and isinstance(f.value, ast.Name) and f.value.id in self.modules:
                    return True
                if f.attr == "of" and isinstance(f.value, ast.Name) and f.value.id in self.ctor:
                    return True
                if f.attr in CONSTRUCTORS | {"of"} and isinstance(f.value, ast.Attribute):
                    return True  # e.g. rt.CobDecimal.of(...), rt.cobdec.dec(...)
            return False
        if isinstance(e, ast.BinOp) and isinstance(e.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            return self.is_dec(e.left, scope) or self.is_dec(e.right, scope)
        if isinstance(e, ast.UnaryOp) and isinstance(e.op, (ast.USub, ast.UAdd)):
            return self.is_dec(e.operand, scope)
        if isinstance(e, ast.IfExp):
            return self.is_dec(e.body, scope) or self.is_dec(e.orelse, scope)
        if isinstance(e, ast.Name):
            return e.id in self.dec_names.get(scope, set()) or \
                (scope is not self.tree and e.id in self.dec_names.get(self.tree, set()))
        return False

    def sites(self):
        for scope in [self.tree, *self.functions.values()]:
            for n in self._own(scope):
                yield from self._site(n, scope)

    def _site(self, n, scope):
        d = lambda e: self.is_dec(e, scope)  # noqa: E731
        if isinstance(n, ast.Compare):
            operands = [n.left, *n.comparators]
            for i, op in enumerate(n.ops):
                left, right = operands[i], operands[i + 1]
                if isinstance(op, (ast.Eq, ast.NotEq)) and (d(left) or d(right)):
                    yield n, "eq"
                elif isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)) and (d(left) or d(right)):
                    yield n, "order"
                elif isinstance(op, (ast.In, ast.NotIn)) and d(left):
                    yield n, "in"
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            if n.func.id in ORDERING_CALLS and any(d(a) or (isinstance(a, (ast.List, ast.Tuple)) and
                                                            any(d(x) for x in a.elts)) for a in n.args):
                yield n, "order"
            elif n.func.id in ("hash", "set", "frozenset") and any(d(a) for a in n.args):
                yield n, "hash"
        elif isinstance(n, ast.Set) and any(d(x) for x in n.elts):
            yield n, "hash"
        elif isinstance(n, ast.Dict) and any(k is not None and d(k) for k in n.keys):
            yield n, "hash"
        elif isinstance(n, (ast.SetComp, ast.DictComp)) and d(n.elt if isinstance(n, ast.SetComp) else n.key):
            yield n, "hash"
        elif isinstance(n, ast.Subscript) and d(n.slice) and not isinstance(n.slice, ast.Slice):
            yield n, "hash"  # x[dec(...)]: a dict key (a list index would fail without __index__)


def scan(text: str) -> list[tuple[int, str, str]]:
    """(line, kind, code) of every site in a translation's source."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    lines = text.splitlines()
    out = {(n.lineno, kind, lines[n.lineno - 1].strip()[:160]) for n, kind in _Scan(tree).sites()}
    return sorted(out)


def generate() -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    for track, name, cond, attempt, rnd, path in translations():
        for line, kind, code in scan(path.read_text(encoding="utf-8")):
            w.writerow({"track": track, "program": name, "condition": cond, "attempt": attempt,
                        "round": rnd, "line": line, "kind": kind, "code": code,
                        "translation": path.relative_to(ROOT).as_posix()})
    return buf.getvalue()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    text = generate()
    if a.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print(f"{OUT} is not what the scan gives now")
            return 1
        print("eq-sites.csv reproduced")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"{text.count(chr(10)) - 1} sites")
    return 0


if __name__ == "__main__":
    sys.exit(main())

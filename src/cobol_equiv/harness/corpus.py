"""Loading corpus programs (corpus/<name>/{program.cob, reference.py, spec.py, mutants.py})."""

from __future__ import annotations

from pathlib import Path

from .check import load_module, load_module_from_source

CORPUS_DIR = Path(__file__).resolve().parents[3] / "corpus"


def program_dirs(root: Path = CORPUS_DIR) -> list[Path]:
    return sorted(p for p in root.iterdir() if (p / "spec.py").exists())


def load_spec(d: Path):
    return load_module(d / "spec.py", f"corpus_spec_{d.name}").SPEC


def load_reference(d: Path):
    return load_module(d / "reference.py", f"corpus_ref_{d.name}")


def load_mutants(d: Path) -> list[dict]:
    p = d / "mutants.py"
    return load_module(p, f"corpus_mut_{d.name}").MUTANTS if p.exists() else []


def apply_mutant(source: str, mutant: dict) -> str:
    """Apply each (find, replace) edit; every `find` must occur exactly once."""
    for find, replace in mutant["edits"]:
        n = source.count(find)
        if n != 1:
            raise ValueError(f"mutant {mutant['id']}: pattern occurs {n} times: {find!r}")
        source = source.replace(find, replace)
    return source


def load_mutated(d: Path, mutant: dict):
    src = (d / "reference.py").read_text(encoding="utf-8")
    return load_module_from_source(apply_mutant(src, mutant), f"mutant_{d.name}_{mutant['id']}",
                                   str(d / f"reference.py[{mutant['id']}]"))

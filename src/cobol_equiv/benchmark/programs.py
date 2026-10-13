"""The benchmark corpus: Track E (benchmark/corpus-e/) and Track R
(corpus/ and benchmark/corpus-r/), see docs/benchmark-protocol.md."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..harness.corpus import load_reference, load_spec

ROOT = Path(__file__).resolve().parents[3]
TRACK_DIRS = {
    "E": [ROOT / "benchmark" / "corpus-e"],
    "R": [ROOT / "corpus", ROOT / "benchmark" / "corpus-r"],
}


@dataclass(frozen=True)
class Program:
    track: str
    dir: Path

    @property
    def name(self) -> str:
        return self.dir.name

    def spec(self):
        return load_spec(self.dir)

    def reference(self):
        return load_reference(self.dir)


def programs(track: str) -> list[Program]:
    out = []
    for root in TRACK_DIRS[track]:
        if root.exists():
            out += [Program(track, d) for d in sorted(root.iterdir()) if (d / "spec.py").exists()]
    return out


def all_programs() -> list[Program]:
    return programs("E") + programs("R")

"""Download the Track E programs that are not committed (see
docs/benchmark-protocol.md, section 1) and apply their adaptations.

    python -m cobol_equiv.benchmark.fetch [--check]

For every `benchmark/corpus-e/<name>/source.json` ({"url", "sha256"}) the
file is downloaded to `original.cob` (unless it is already there with the
right checksum), its SHA-256 is checked, and `program.cob` is written from
it by applying the (find, replace) edits of `adaptation.json`, if present;
each `find` must occur exactly once. With "task_url" and "task_sha256" the
task statement is downloaded to `task.txt` too (for sample inputs given in
the task). None of these files is committed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CORPUS_E = ROOT / "benchmark" / "corpus-e"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def adapt(source: str, edits: list) -> str:
    for find, replace in edits:
        n = source.count(find)
        if n != 1:
            raise ValueError(f"edit pattern occurs {n} times: {find!r}")
        source = source.replace(find, replace)
    return source


def _download(url: str, attempts: int = 5) -> bytes:
    """GET with retries (2, 4, 8, 16 s apart) on network errors."""
    import time
    import urllib.error

    for i in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:  # noqa: S310 (pinned URL)
                return r.read()
        except (urllib.error.URLError, OSError):
            if i == attempts - 1:
                raise
            time.sleep(2 ** (i + 1))
    raise AssertionError("unreachable")


def _get(path: Path, url: str, sha: str, offline: bool) -> bytes:
    data = path.read_bytes() if path.exists() else b""
    if _sha(data) != sha:
        if offline:
            raise SystemExit(f"{path}: missing or changed")
        data = _download(url)
        if _sha(data) != sha:
            raise SystemExit(f"SHA-256 mismatch for {url}")
        path.write_bytes(data)
    return data


def fetch_one(d: Path, offline: bool = False) -> None:
    meta = json.loads((d / "source.json").read_text(encoding="utf-8"))
    data = _get(d / "original.cob", meta["url"], meta["sha256"], offline)
    if "task_url" in meta:
        _get(d / "task.txt", meta["task_url"], meta["task_sha256"], offline)
    text = data.decode("utf-8")
    ad = d / "adaptation.json"
    edits = json.loads(ad.read_text(encoding="utf-8"))["edits"] if ad.exists() else []
    (d / "program.cob").write_text(adapt(text, edits), encoding="utf-8", newline="")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="do not download; verify local copies")
    a = ap.parse_args(argv)
    for d in sorted(CORPUS_E.iterdir()):
        if (d / "source.json").exists():
            fetch_one(d, offline=a.check)
    return 0


if __name__ == "__main__":
    sys.exit(main())

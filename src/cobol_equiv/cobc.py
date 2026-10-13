"""Locating and describing the GnuCOBOL compiler used as the oracle.

The compiler is `cobc` on PATH, or the one named by the COBC environment
variable (for example /opt/gnucobol-3.2/bin/cobc). Results are kept per
compiler version, in results/gnucobol-<version>/.
"""

from __future__ import annotations

import functools
import os
import re
import shutil
import subprocess
from pathlib import Path

# Flags used for every compile. -std=default selects the GnuCOBOL default
# dialect (binary-truncate, binary-size, sign encoding).
COBC_FLAGS = ("-x", "-std=default")


def cobc_path() -> str | None:
    return shutil.which(os.environ.get("COBC", "cobc"))


def _private_libdir(cobc: str | None) -> str | None:
    """lib/ next to a cobc installed under its own prefix (a source build)."""
    if cobc is None:
        return None
    lib = Path(cobc).resolve().parent.parent / "lib"
    return str(lib) if any(lib.glob("libcob.so*")) else None


def clean_env() -> dict[str, str]:
    """Environment for compiling and running COBOL.

    Drops every inherited GnuCOBOL setting (COB_*, COBC*, COBCPY, ...), so a
    developer's copybook path or runtime options cannot change results.
    LD_LIBRARY_PATH is replaced: it points at the libcob that belongs to the
    selected cobc when that cobc lives under its own prefix, and is removed
    otherwise. Mixing a program compiled by one version with another
    version's libcob gives wrong results.
    """
    env = {k: v for k, v in os.environ.items()
           if not k.upper().startswith("COB") and k != "LD_LIBRARY_PATH"}
    lib = _private_libdir(cobc_path())
    if lib:
        env["LD_LIBRARY_PATH"] = lib
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    return env


@functools.lru_cache(maxsize=None)
def _version_of(path: str) -> str:
    env = {k: v for k, v in clean_env().items()}
    out = subprocess.run([path, "--version"], capture_output=True, check=True, env=env)
    return out.stdout.decode("utf-8", "replace").splitlines()[0].strip()


def cobc_version() -> str:
    """First line of `cobc --version`, e.g. 'cobc (GnuCOBOL) 3.1.2.0'."""
    path = cobc_path()
    if path is None:
        raise RuntimeError("cobc not found on PATH")
    return _version_of(path)


def version_label(version_line: str | None = None) -> str:
    """'cobc (GnuCOBOL) 3.1.2.0' -> '3.1.2', 'cobc (GnuCOBOL) 3.2.0' -> '3.2'."""
    line = version_line or cobc_version()
    m = re.search(r"(\d+(?:\.\d+)+)", line)
    if not m:
        raise RuntimeError(f"cannot parse cobc version from {line!r}")
    parts = m.group(1).split(".")
    while len(parts) > 2 and parts[-1] == "0":
        parts.pop()
    return ".".join(parts)


def results_dir(base: str | Path = "results") -> Path:
    return Path(base) / f"gnucobol-{version_label()}"

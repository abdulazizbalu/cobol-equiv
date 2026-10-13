"""Locating and describing the GnuCOBOL compiler used as the oracle."""

from __future__ import annotations

import os
import shutil
import subprocess

# Flags used for every oracle and corpus compile. -std=default selects the
# GnuCOBOL default dialect, whose settings (binary-truncate, binary-size,
# sign encoding) the runtime documents and is validated against.
COBC_FLAGS = ("-x", "-std=default")


def cobc_path() -> str | None:
    return shutil.which(os.environ.get("COBC", "cobc"))


def clean_env() -> dict[str, str]:
    """Environment for compiling and running COBOL: no inherited COB_* settings."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("COB_")}
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    return env


def cobc_version() -> str:
    """First line of `cobc --version`, e.g. 'cobc (GnuCOBOL) 3.1.2.0'."""
    path = cobc_path()
    if path is None:
        raise RuntimeError("cobc not found on PATH")
    out = subprocess.run(
        [path, "--version"], capture_output=True, check=True, env=clean_env()
    ).stdout.decode("utf-8", "replace")
    return out.splitlines()[0].strip()

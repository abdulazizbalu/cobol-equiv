"""Locating and describing the GnuCOBOL compiler used as the oracle."""

from __future__ import annotations

import os
import shutil
import subprocess

# Flags used for every compile. -std=default selects the GnuCOBOL default
# dialect (binary-truncate, binary-size, sign encoding).
COBC_FLAGS = ("-x", "-std=default")


def cobc_path() -> str | None:
    return shutil.which(os.environ.get("COBC", "cobc"))


def clean_env() -> dict[str, str]:
    """Environment for compiling and running COBOL.

    Drops every inherited GnuCOBOL setting (COB_*, COBC*, COBCPY, ...), so a
    developer's copybook path or runtime options cannot change results.
    """
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("COB")}
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

import os

import pytest

from cobol_equiv.cobc import cobc_path


def pytest_collection_modifyitems(config, items):
    """Skip oracle tests when cobc is missing, unless COBOL_EQUIV_REQUIRE_COBC=1 (CI)."""
    if cobc_path() is not None:
        return
    if os.environ.get("COBOL_EQUIV_REQUIRE_COBC") == "1":
        raise pytest.UsageError("cobc not found but COBOL_EQUIV_REQUIRE_COBC=1")
    skip = pytest.mark.skip(reason="cobc not on PATH")
    for item in items:
        if "oracle" in item.keywords:
            item.add_marker(skip)

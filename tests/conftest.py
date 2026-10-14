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


# COBOL_EQUIV_TRAP_COMPARISONS=1 (CI): record every CobDecimal comparison or
# hash call made in the test process and fail the session if one comes from
# outside the comparison tests. Runtime 1.0.0, frozen for the benchmark, had
# no such methods (deviation D14), so a call here would be a harness, oracle
# or reference path whose result the runtime fix changed.
_COMPARISON_TESTS = ("tests/oracle/test_compare.py",)
_calls: dict = {}


def pytest_configure(config):
    if os.environ.get("COBOL_EQUIV_TRAP_COMPARISONS") != "1":
        return
    import traceback

    from cobol_equiv.runtime.cobdec import CobDecimal

    def wrap(name):
        orig = getattr(CobDecimal, name)

        def method(*args):
            caller = traceback.extract_stack(limit=2)[0]
            key = (name, os.path.relpath(caller.filename), caller.lineno)
            _calls[key] = _calls.get(key, 0) + 1
            return orig(*args)
        return method

    for name in ("__eq__", "__ne__", "__lt__", "__le__", "__gt__", "__ge__", "__hash__"):
        setattr(CobDecimal, name, wrap(name))


def pytest_sessionfinish(session, exitstatus):
    outside = {k: v for k, v in _calls.items() if not k[1].replace(os.sep, "/").endswith(_COMPARISON_TESTS)}
    if outside:
        for (name, path, line), n in sorted(outside.items()):
            print(f"CobDecimal.{name} called {n} time(s) at {path}:{line}")
        session.exitstatus = 1

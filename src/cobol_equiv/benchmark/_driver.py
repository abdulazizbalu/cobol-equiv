"""Child-process driver for running one translation (standard library only).

    python driver.py <request.json> <result.json>

The request holds the translation path, the inputs (never the expected
outputs), the per-vector time limit and, optionally, the number of
time-outs after which to stop. The result file gets one JSON line per
vector, written as soon as the vector is done (so the results of finished
vectors survive if the parent stops the process at its total time limit):
the outputs or the exception, and the number of Unsupported errors raised.

The time limit also covers loading the module. If a translation swallows
the time-out exception and is still running GRACE seconds later, the vector
is recorded as timed out and the process ends; the parent records the
vectors not reached as timed out too ("abandoned"). The file paths are
removed from sys.argv before the translation is loaded, and the result file
is not in the working directory.

The request's "runtime" selects the comparison behaviour of CobDecimal
(deviation D14): "registered" is that of runtime 1.0.0, frozen for the
benchmark (no comparison methods: == and != compare identity, ordering
raises TypeError, hash is the identity hash); "corrected" is the value
comparison of the installed runtime (1.1.0). In both modes each result line
carries "cmp": the == / != calls on a CobDecimal ("eq"), how many of them a
runtime of the other mode would answer differently ("eq_diff"), and the
ordering and hash calls. Calls made while the module is loaded are added
to the counts of every vector, like its Unsupported hits.
"""

import base64
import importlib.util
import io
import json
import os
import signal
import sys
import traceback

GRACE = 2


class VectorTimeout(BaseException):
    pass


_state = {"fired": False, "emit": None}


def _alarm(signum, frame):
    if not _state["fired"]:
        _state["fired"] = True
        signal.alarm(GRACE)
        raise VectorTimeout()
    # the translation caught the time-out and kept running
    _state["emit"]({"timeout": True, "unsupported": 0})
    _state["emit"]({"abandoned": True})
    os._exit(0)


def _arm(seconds):
    _state["fired"] = False
    signal.alarm(max(1, int(seconds)))


def _disarm():
    signal.alarm(0)
    _state["fired"] = False


def _hits():
    try:
        from cobol_equiv.runtime.errors import unsupported_hits
    except ImportError:
        return 0
    return unsupported_hits()


def _reset():
    try:
        from cobol_equiv.runtime.errors import reset_unsupported_hits
    except ImportError:
        return
    reset_unsupported_hits()


_CMP = {"eq": 0, "eq_diff": 0, "order": 0, "hash": 0}
_ORDER = {"__lt__": "<", "__le__": "<=", "__gt__": ">", "__ge__": ">="}


def _setup_runtime(mode):
    """Install the comparison methods of the mode on CobDecimal, counting
    the calls in _CMP. Nothing to do when the runtime is not importable
    (condition C)."""
    if mode is None:
        return
    try:
        from cobol_equiv.runtime.cobdec import CobDecimal
    except ImportError:
        return
    value_eq = CobDecimal.__eq__
    registered = mode == "registered"
    if not registered and mode != "corrected":
        raise ValueError(f"unknown runtime mode {mode!r}")

    def differs(a, b):
        try:
            v = value_eq(a, b)
        except ArithmeticError:
            return True  # a NaN: False with identity ==, an error with value ==
        return v is not NotImplemented and v != (a is b)

    def eq(a, b):
        _CMP["eq"] += 1
        _CMP["eq_diff"] += differs(a, b)
        if registered:
            return (a is b) if isinstance(b, CobDecimal) else NotImplemented
        return value_eq(a, b)

    def ne(a, b):
        r = eq(a, b)
        return r if r is NotImplemented else not r

    def ordering(name):
        value_op = getattr(CobDecimal, name)

        def op(a, b):
            _CMP["order"] += 1
            if not registered:
                return value_op(a, b)
            if isinstance(b, CobDecimal):  # the message Python gives without the method
                raise TypeError(f"'{_ORDER[name]}' not supported between instances of "
                                "'CobDecimal' and 'CobDecimal'")
            return NotImplemented
        return op

    value_hash = CobDecimal.__hash__

    def hash_(a):
        _CMP["hash"] += 1
        return object.__hash__(a) if registered else value_hash(a)

    for name in _ORDER:
        setattr(CobDecimal, name, ordering(name))
    CobDecimal.__eq__, CobDecimal.__ne__, CobDecimal.__hash__ = eq, ne, hash_


def _cmp_counts():
    r = dict(_CMP)
    for k in _CMP:
        _CMP[k] = 0
    return r


def _err(e: BaseException) -> str:
    return f"{type(e).__name__}: {e}"[:500]


def main() -> int:
    req_path, res_path = sys.argv[1], sys.argv[2]
    sys.argv = sys.argv[:1]
    with open(req_path, encoding="utf-8") as fh:
        req = json.load(fh)
    out_fh = open(res_path, "w", encoding="utf-8")

    def emit(r):
        out_fh.write(json.dumps(r) + "\n")
        out_fh.flush()

    _state["emit"] = emit
    signal.signal(signal.SIGALRM, _alarm)
    real_stdout = sys.stdout
    sys.stdout = io.StringIO()  # prints of the translation are not its output
    _reset()
    _setup_runtime(req.get("runtime"))
    load_error = None
    mod = None
    _arm(req["timeout"])
    try:
        spec = importlib.util.spec_from_file_location("translation", req["module"])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _disarm()
        if not callable(getattr(mod, "main", None)):
            load_error = "AttributeError: the module has no main function"
    except VectorTimeout:
        _disarm()
        load_error = "timeout"
    except BaseException as e:  # noqa: BLE001 (any failure of the translation is a result)
        _disarm()
        load_error = _err(e)
    import_hits = _hits()
    # comparisons made while the module was loaded: added to every vector's
    # counts, like the Unsupported hits of the import
    import_cmp = _cmp_counts()

    def cmp_with_import(counts):
        return {k: counts.get(k, 0) + import_cmp[k] for k in import_cmp}

    timeouts = 0
    for vec in req["vectors"]:
        if req.get("max_timeouts") and timeouts >= req["max_timeouts"]:
            break  # the parent marks the rest as timed out without running them
        if load_error == "timeout":
            emit({"timeout": True, "unsupported": import_hits, "cmp": cmp_with_import({})})
            continue
        if load_error is not None:
            emit({"error": load_error, "unsupported": import_hits, "cmp": cmp_with_import({})})
            continue
        stdin = base64.b64decode(vec.get("stdin", ""))
        files = {k: base64.b64decode(v) for k, v in vec.get("files", {}).items()}
        _reset()
        _cmp_counts()
        _arm(req["timeout"])
        try:
            out, out_files = mod.main(stdin, dict(files))
            late = _state["fired"]  # the time-out fired and was swallowed
            _disarm()
            if late:
                raise VectorTimeout()
            if not isinstance(out, (bytes, bytearray)) or not isinstance(out_files, dict):
                raise TypeError("main must return (bytes, dict)")
            enc_files = {}
            for k, v in out_files.items():
                if not isinstance(v, (bytes, bytearray)):
                    raise TypeError(f"output file {k!r} is not bytes")
                enc_files[str(k)] = base64.b64encode(bytes(v)).decode("ascii")
            r = {"stdout": base64.b64encode(bytes(out)).decode("ascii"), "files": enc_files}
        except VectorTimeout:
            _disarm()
            r = {"timeout": True}
            timeouts += 1
        except BaseException as e:  # noqa: BLE001
            _disarm()
            r = {"error": _err(e), "trace": traceback.format_exc()[-1500:]}
        r["unsupported"] = _hits() + import_hits
        r["cmp"] = cmp_with_import(_cmp_counts())
        emit(r)
    sys.stdout = real_stdout
    out_fh.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

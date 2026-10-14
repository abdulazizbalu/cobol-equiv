"""Child-process driver for running one translation (standard library only).

    python driver.py <request.json> <result.json>

The request holds the translation path, the inputs (never the expected
outputs), the per-vector time limit and whether the runtime's Unsupported
counter should be read. The result file gets one JSON line per vector, written
as soon as the vector is done (so the results of finished vectors survive if
the parent stops the process at its total time limit): the outputs or the
exception, and the number of Unsupported errors raised.
"""

import base64
import importlib.util
import io
import json
import signal
import sys
import traceback


class VectorTimeout(BaseException):
    pass


def _alarm(signum, frame):
    raise VectorTimeout()


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


def _err(e: BaseException) -> str:
    return f"{type(e).__name__}: {e}"[:500]


def main() -> int:
    req_path, res_path = sys.argv[1], sys.argv[2]
    with open(req_path, encoding="utf-8") as fh:
        req = json.load(fh)
    signal.signal(signal.SIGALRM, _alarm)
    real_stdout = sys.stdout
    sys.stdout = io.StringIO()  # prints of the translation are not its output
    _reset()
    load_error = None
    mod = None
    try:
        spec = importlib.util.spec_from_file_location("translation", req["module"])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not callable(getattr(mod, "main", None)):
            load_error = "AttributeError: the module has no main function"
    except BaseException as e:  # noqa: BLE001 (any failure of the translation is a result)
        load_error = _err(e)
    import_hits = _hits()
    out_fh = open(res_path, "w", encoding="utf-8")

    def emit(r):
        out_fh.write(json.dumps(r) + "\n")
        out_fh.flush()

    for vec in req["vectors"]:
        if load_error is not None:
            emit({"error": load_error, "unsupported": import_hits})
            continue
        stdin = base64.b64decode(vec.get("stdin", ""))
        files = {k: base64.b64decode(v) for k, v in vec.get("files", {}).items()}
        _reset()
        signal.alarm(max(1, int(req["timeout"])))
        try:
            out, out_files = mod.main(stdin, dict(files))
            signal.alarm(0)
            if not isinstance(out, (bytes, bytearray)) or not isinstance(out_files, dict):
                raise TypeError("main must return (bytes, dict)")
            enc_files = {}
            for k, v in out_files.items():
                if not isinstance(v, (bytes, bytearray)):
                    raise TypeError(f"output file {k!r} is not bytes")
                enc_files[str(k)] = base64.b64encode(bytes(v)).decode("ascii")
            r = {"stdout": base64.b64encode(bytes(out)).decode("ascii"), "files": enc_files}
        except VectorTimeout:
            r = {"timeout": True}
        except BaseException as e:  # noqa: BLE001
            signal.alarm(0)
            r = {"error": _err(e), "trace": traceback.format_exc()[-1500:]}
        r["unsupported"] = _hits() + import_hits
        emit(r)
    sys.stdout = real_stdout
    out_fh.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

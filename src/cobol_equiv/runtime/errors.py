"""Exceptions raised by the runtime."""

_hits = 0


class Unsupported(NotImplementedError):
    """A COBOL construct or data case outside the documented, oracle-checked
    subset. The runtime refuses it instead of guessing GnuCOBOL's behaviour.

    Every instance is counted, so the harness can report a translation that
    caught the exception and carried on (see unsupported_hits())."""

    def __init__(self, *args):
        global _hits
        _hits += 1
        super().__init__(*args)


def unsupported_hits() -> int:
    """Number of Unsupported errors raised since the last reset."""
    return _hits


def reset_unsupported_hits() -> None:
    global _hits
    _hits = 0

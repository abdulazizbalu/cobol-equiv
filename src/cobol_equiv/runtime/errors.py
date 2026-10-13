"""Exceptions raised by the runtime."""


class Unsupported(NotImplementedError):
    """A COBOL construct or data case outside the documented, oracle-checked
    subset. The runtime refuses it instead of guessing GnuCOBOL's behaviour."""

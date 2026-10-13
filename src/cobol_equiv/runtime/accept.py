"""ACCEPT from standard input (libcob `cob_accept`, no screen section).

    inp = Stdin(stdin_bytes)
    inp.accept(ws["N"])      # ACCEPT N

Each ACCEPT reads one line (without its newline). After the last line,
GnuCOBOL supplies a single space. The line is then MOVEd as alphanumeric
data to the receiver; for a numeric USAGE DISPLAY receiver it is first cut
to the receiver's length in bytes.
"""

from __future__ import annotations

from . import encoding as enc
from .move import alnum_text_to_numeric, move
from .pic import NUMERIC, NUMERIC_EDITED
from .storage import FieldRef


class Stdin:
    def __init__(self, data: bytes):
        self._lines = data.split(b"\n")
        if self._lines and self._lines[-1] == b"":
            self._lines.pop()
        self._pos = 0

    def read_line(self) -> bytes:
        """The next line, or b" " at end of input."""
        if self._pos >= len(self._lines):
            return b" "
        self._pos += 1
        return self._lines[self._pos - 1]

    def accept(self, ref: FieldRef) -> None:
        accept_line(self.read_line(), ref)


def accept_line(line: bytes, ref: FieldRef) -> None:
    """Store an input line as ACCEPT does."""
    if ref.category in (NUMERIC, NUMERIC_EDITED):
        if ref.category == NUMERIC and ref.usage == enc.DISPLAY:
            line = line[:ref.size]
        alnum_text_to_numeric(line, ref)
    else:
        move(line, ref)

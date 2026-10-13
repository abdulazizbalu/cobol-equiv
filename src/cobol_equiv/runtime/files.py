"""Sequential files as byte strings, matching GnuCOBOL 3.1.2 behaviour.

LINE SEQUENTIAL (ORGANIZATION IS LINE SEQUENTIAL), checked by the corpus
programs that use files:
  * READ: one record per line; a short line is padded with spaces, a long
    line is truncated (the rest of that line is skipped); a carriage return
    before the newline is dropped; a last line without newline is still read.
  * WRITE: trailing spaces of the record are removed, then a newline is added.

RECORD SEQUENTIAL (ORGANIZATION IS SEQUENTIAL, fixed-length records): the
records are concatenated without separators.
"""

from __future__ import annotations

from typing import Iterator

from .storage import FieldRef


class LineSequentialReader:
    def __init__(self, data: bytes, record_size: int):
        self.size = record_size
        lines = data.split(b"\n")
        if lines and lines[-1] == b"":
            lines.pop()
        self._lines: Iterator[bytes] = iter(lines)

    def read(self, into: FieldRef | None = None) -> bytes | None:
        """Next record (padded/truncated), or None at end of file.
        If `into` is given (the FD record), the record is stored there."""
        line = next(self._lines, None)
        if line is None:
            return None
        if line.endswith(b"\r"):
            line = line[:-1]
        rec = line[: self.size].ljust(self.size, b" ")
        if into is not None:
            into.set_raw(rec)
        return rec


class LineSequentialWriter:
    def __init__(self):
        self._buf = bytearray()

    def write(self, record) -> None:
        data = record.raw if isinstance(record, FieldRef) else bytes(record)
        self._buf += data.rstrip(b" ") + b"\n"

    def getvalue(self) -> bytes:
        return bytes(self._buf)


class RecordSequentialReader:
    def __init__(self, data: bytes, record_size: int):
        if len(data) % record_size:
            raise ValueError("file size is not a multiple of the record size")
        self._recs = iter(data[i:i + record_size] for i in range(0, len(data), record_size))

    def read(self, into: FieldRef | None = None) -> bytes | None:
        rec = next(self._recs, None)
        if rec is not None and into is not None:
            into.set_raw(rec)
        return rec


class RecordSequentialWriter:
    def __init__(self):
        self._buf = bytearray()

    def write(self, record) -> None:
        self._buf += record.raw if isinstance(record, FieldRef) else bytes(record)

    def getvalue(self) -> bytes:
        return bytes(self._buf)

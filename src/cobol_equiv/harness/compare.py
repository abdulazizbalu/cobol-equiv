"""Byte-exact comparison of COBOL and translation outputs, with a readable
report of the first difference."""

from __future__ import annotations

from dataclasses import dataclass

from .spec import STDOUT, OutputLayout


@dataclass
class Difference:
    stream: str  # "<stdout>" or an output file name
    line: int  # 1-based line (or record), 0 when the stream is missing
    column: int  # 1-based byte column within the line
    field: str | None
    expected: bytes  # GnuCOBOL
    actual: bytes  # translation
    detail: str = ""

    def describe(self) -> str:
        if self.detail:
            return f"{self.stream}: {self.detail}"
        where = f"{self.stream} line {self.line}"
        if self.field:
            where += f", field {self.field}"
        else:
            where += f", column {self.column}"
        return f"{where}: expected {self.expected!r}, got {self.actual!r}"


def _lines(data: bytes, record_length: int | None = None) -> list[bytes]:
    if record_length:
        return [data[i:i + record_length] for i in range(0, len(data), record_length)]
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    return lines


def first_difference(stream: str, expected: bytes | None, actual: bytes | None,
                     layout: OutputLayout | None = None) -> Difference | None:
    if expected == actual:
        return None
    if expected is None or actual is None:
        what = "file not produced by GnuCOBOL" if expected is None else "file missing from translation output"
        return Difference(stream, 0, 0, None, expected or b"", actual or b"", what)
    rl = layout.record_length if layout else None
    el, al = _lines(expected, rl), _lines(actual, rl)
    for n in range(max(len(el), len(al))):
        e = el[n] if n < len(el) else None
        a = al[n] if n < len(al) else None
        if e == a:
            continue
        if e is None or a is None:
            return Difference(stream, n + 1, 1, None, e or b"", a or b"",
                              f"line {n + 1}: " + ("extra line in translation output " + repr(a)
                                                   if e is None else "line missing from translation output, expected " + repr(e)))
        col = next((i for i in range(min(len(e), len(a))) if e[i] != a[i]), min(len(e), len(a)))
        fields = layout.select(e) if layout else None
        if fields:
            for name, start, length in fields:
                if start <= col < start + length:
                    return Difference(stream, n + 1, col + 1, name,
                                      e[start:start + length], a[start:start + length])
        lo = max(0, col - 10)
        return Difference(stream, n + 1, col + 1, None, e[lo:col + 20], a[lo:col + 20])
    return Difference(stream, len(el), 1, None, expected[-20:], actual[-20:],
                      "same lines, but the final newline differs")


def compare(expected_stdout: bytes, expected_files: dict, actual_stdout: bytes, actual_files: dict,
            outputs: list[str], layouts: dict[str, OutputLayout]) -> Difference | None:
    d = first_difference(STDOUT, expected_stdout, actual_stdout, layouts.get(STDOUT))
    if d:
        return d
    for name in outputs:
        d = first_difference(name, expected_files.get(name), actual_files.get(name), layouts.get(name))
        if d:
            return d
    return None


def columns(*widths: tuple[str, int]) -> list[tuple[str, int, int]]:
    """Helper: columns(("NAME", 10), ("AMOUNT", 9)) -> [(name, start, length), ...]."""
    out, pos = [], 0
    for name, w in widths:
        out.append((name, pos, w))
        pos += w
    return out

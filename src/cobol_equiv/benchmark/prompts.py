"""Prompts for the translators (docs/benchmark-protocol.md, section 7).

    python -m cobol_equiv.benchmark.prompts --program NAME --condition A|C [--out FILE]

prints (or writes) the filled-in prompt of a program.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..harness.spec import STDIN
from .programs import Program, all_programs
from .vectors import PRIMARY, decode_input, load, unb64

ROOT = Path(__file__).resolve().parents[3]
SHEET = ROOT / "benchmark" / "prompts" / "api-sheet.md"
LITERAL_LIMIT = 4000
MESSAGE_LIMIT = 500

IO_CONTRACT = """\
The Python module must define

    def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]

- stdin: everything the program reads with ACCEPT (one ACCEPT reads one line).
- input_files: for every file the program reads, the name in its ASSIGN
  clause mapped to the full content of the file. LINE SEQUENTIAL files are
  lines that end with "\\n"; SEQUENTIAL files are fixed-length records
  without separators.
- The return value is all bytes the program writes to standard output, and
  a dict that maps the ASSIGN name of every file the program opens for
  output to the full content of that file.
- The module must not read the clock, random sources, the network or the
  file system, and must not start processes. It runs on Python 3.12."""

HEAD = """\
Translate the COBOL program below into a Python module.

The module must behave exactly like the program compiled with GnuCOBOL 3.1.2
(cobc -x -std=default): for every input whose records fit the program's
record descriptions, it must produce byte for byte the same standard output
and output files.

"""

USE_RUNTIME = """\
Use the Python package cobol_equiv.runtime, documented in the API reference
below, for COBOL data and statements. Besides it, use only the Python
standard library."""

USE_STDLIB = """\
Use only the Python standard library. The module runs in an interpreter
that has no other packages."""

TAIL_ONE_SHOT = """\
Reply with the complete Python module in one ```python code block. Do not
write anything after the code block."""

TAIL_REPAIR = """\
Fix the translation. Reply with the complete corrected Python module in one
```python code block. Do not write anything after the code block."""


# ---- source shown to the translator -----------------------------------------

def _strip_inline_comment(line: str) -> str:
    """Cut a `*>` comment that is outside string literals."""
    quote = None
    i = 0
    while i < len(line):
        c = line[i]
        if quote:
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif line.startswith("*>", i):
            return line[:i]
        i += 1
    return line


def shown_source(text: str, free: bool) -> str:
    """The COBOL source with comment lines, `*>` comments and (fixed format)
    columns 73-80 removed (protocol, section 1). Lines that become blank
    because of a removal are dropped; other blank lines are kept."""
    out = []
    for line in text.splitlines():
        original = line
        if not free:
            line = line[:72]
            if len(line) >= 7 and line[6] in "*/":
                continue
        else:
            if line.lstrip().startswith("*>"):
                continue
        line = _strip_inline_comment(line).rstrip()
        if not line and original.strip():
            continue
        out.append(line)
    return "\n".join(out) + "\n"


# ---- examples and feedback ---------------------------------------------------

def _literal(data: bytes, cut: bool = True) -> str:
    text = repr(bytes(data))
    if cut and len(text) > LITERAL_LIMIT:
        text = text[:LITERAL_LIMIT] + "...(cut)"
    return text


def _files_literal(files: dict, cut: bool = True) -> str:
    items = []
    for name in sorted(files):
        v = files[name]
        items.append(f"{name!r}: {'None' if v is None else _literal(v, cut)}")
    return "{" + ", ".join(items) + "}"


def input_lines(inp: dict, cut: bool = True) -> str:
    """Input literals; cut at LITERAL_LIMIT characters only in feedback."""
    files = {k: v for k, v in inp.items() if k != STDIN}
    return f"stdin = {_literal(inp.get(STDIN, b''), cut)}\ninput_files = {_files_literal(files, cut)}"


def examples(doc: dict) -> str:
    parts = []
    for k, v in enumerate(doc["sets"]["visible"], 1):
        exp = v["expected"][PRIMARY]
        files = {n: (None if b is None else unb64(b)) for n, b in exp["files"].items()}
        parts.append(f"### Example {k}\n{input_lines(decode_input(v['input']), cut=False)}\n"
                     f"expected stdout = {_literal(unb64(exp['stdout']), cut=False)}\n"
                     f"expected output_files = {_files_literal(files, cut=False)}")
    return "\n\n".join(parts)


def feedback(inp: dict, verdict) -> str:
    """Feedback text for the first failing DEV vector (prompt B)."""
    head = input_lines(inp)
    if verdict.kind == "difference":
        return f"{head}\nFirst difference: {verdict.detail}"
    if verdict.kind == "timeout":
        return f"{head}\nThe translation timed out."
    if verdict.kind == "no code":
        return f"{head}\nNo Python code block was found in the reply."
    msg = verdict.detail
    if verdict.kind == "unsupported" and not msg.startswith(("Unsupported", "MoveError", "PicError",
                                                             "DataError")):
        # Unsupported was raised and caught inside the translation
        return f"{head}\nThe translation {msg} (Unsupported was raised and caught)."
    if len(msg) > MESSAGE_LIMIT:
        msg = msg[:MESSAGE_LIMIT]
    return f"{head}\nThe translation raised {msg}"


# ---- prompts -----------------------------------------------------------------

def source_of(p: Program) -> str:
    spec = p.spec()
    return shown_source(Path(spec.source).read_text(encoding="utf-8"), spec.free_format)


def base_prompt(p: Program, condition: str) -> str:
    doc = load(p)
    text = HEAD + (USE_STDLIB if condition == "C" else USE_RUNTIME) + "\n\n"
    text += f"## IO contract\n{IO_CONTRACT}\n\n"
    text += f"## Examples\nThese are inputs and the exact outputs of the COBOL program.\n{examples(doc)}\n\n"
    if condition != "C":
        text += f"## API reference: cobol_equiv.runtime\n{SHEET.read_text(encoding='utf-8').rstrip()}\n\n"
    text += f"## COBOL program\n```cobol\n{source_of(p)}```\n\n"
    return text


def prompt_one_shot(p: Program, condition: str) -> str:
    return base_prompt(p, condition) + TAIL_ONE_SHOT + "\n"


def prompt_repair(p: Program, current: str, feedback_text: str) -> str:
    return (base_prompt(p, "A") + f"## Your previous translation\n```python\n{current.rstrip()}\n```\n\n"
            "## Test result\nThe previous translation was run on a test input that is not one of the\n"
            f"examples above.\n{feedback_text}\n\n" + TAIL_REPAIR + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--program", required=True)
    ap.add_argument("--condition", choices=["A", "C"], default="A")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    p = next(p for p in all_programs() if p.name == a.program)
    text = prompt_one_shot(p, a.condition)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

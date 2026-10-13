"""Generate the API reference sheet shown to translators in conditions A
and B (docs/benchmark-protocol.md, section 7): the signatures of the
public names of cobol_equiv.runtime and cobol_equiv.runtime.files, each
with a reviewed description of how to call it. Every public name must have
an entry or be listed as internal; a new name stops the generation.

    python -m cobol_equiv.benchmark.apisheet [--check]

Writes benchmark/prompts/api-sheet.md. The committed sheet is the one used;
--check fails if the generated text differs from it.
"""

from __future__ import annotations

import argparse
import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SHEET = ROOT / "benchmark" / "prompts" / "api-sheet.md"

INTRO = """\
`cobol_equiv.runtime` models COBOL data items and statements in Python.
Data is described with Storage, Group, Num, Alnum, Edited and Filler;
every item is a FieldRef at a fixed offset of one bytearray, so REDEFINES,
group moves and record I/O work on the actual bytes. Statements are
functions. Numeric operands may be FieldRefs, ints, Decimals, numeric
strings ("0.05") or CobDecimal values from dec(). A function raises
Unsupported, MoveError or PicError for a case outside the modelled subset.

```python
from cobol_equiv.runtime import Storage, Group, Num, Alnum, Edited, COMP3, move, add, compute, dec
ws = Storage("WS", [
    Num("AMOUNT", "S9(5)V99", usage=COMP3, value="0"),
    Group("IN-DATE", [Num("YYYY", "9(4)"), Num("MM", "99"), Num("DD", "99")]),
    Num("IN-DATE-N", "9(8)", redefines="IN-DATE"),
    Group("ENTRY", [Alnum("CODE", "X(3)"), Num("QTY", "9(3)")], occurs=10),
])
ws["AMOUNT"]       # FieldRef
ws.f("QTY", 3)     # QTY (3); subscripts are 1-based, outermost first
compute(ws["AMOUNT"], dec(ws.f("QTY", 3)) * dec("1.5"), rounded=True)
```
"""

# (module attribute, reviewed description). The descriptions say how to
# call each name; they are written for this sheet and do not describe
# GnuCOBOL behaviours (docs/benchmark-protocol.md, section 7).
ENTRIES = [
    ("Storage", "A record or WORKING-STORAGE area. `items`: list of Item from Num, Alnum, "
     "Edited, Filler, Group. Without `area` the storage is initialised as COBOL does (VALUE "
     "clauses applied). `st[name]` returns the FieldRef of a data name (first occurrence); "
     "`st.f(name, *subs)` the FieldRef of a subscripted item; `st.record()` the whole area as "
     "one FieldRef (for READ ... INTO it). Data names must be unique within one Storage."),
    ("Group", "Group item. `children`: list of Item. `occurs`: OCCURS n. `redefines`: name of "
     "an earlier sibling."),
    ("Num", "Numeric item, e.g. Num(\"BAL\", \"S9(5)V99\", usage=COMP3, value=\"0\"). usage: "
     "DISPLAY (default), COMP, COMP3, COMP5. value: VALUE clause (number, numeric string or "
     "figurative constant)."),
    ("Alnum", "Alphanumeric (PIC X) or alphabetic (PIC A) item."),
    ("Edited", "Numeric-edited item, e.g. Edited(\"OUT\", \"ZZ,ZZ9.99-\")."),
    ("Filler", "Unnamed item (FILLER), e.g. Filler(\"X(3)\", \" - \")."),
    ("FieldRef", "One item at a position in a storage area. Properties: `raw` (bytes), "
     "`text` (str, latin-1), `value` (Decimal, numeric items only), `pic`, `usage`, "
     "`category`. `set_raw(bytes)` replaces the bytes (same length). `int(ref)` gives the "
     "integer value."),
    ("refmod", "Reference modification: refmod(ref, start, length) is `ref (start:length)`, "
     "refmod(ref, start) is `ref (start:)`. The result is an alphanumeric FieldRef sharing the "
     "item's storage, usable as sender or receiver."),
    ("move", "MOVE src TO each of dsts. src: a FieldRef, an alphanumeric literal (str or "
     "bytes), a numeric literal (int or Decimal) or a figurative constant (SPACES, ZEROS, HIGH_VALUES, LOW_VALUES, "
     "All(\"x\"))."),
    ("initialize", "INITIALIZE f (no REPLACING phrase)."),
    ("add", "ADD operands TO targets. operands: one operand or a list. targets: a FieldRef, "
     "(FieldRef, rounded) or a list of these. Returns True if a size error occurred; pass "
     "on_size_error=True when the statement has ON SIZE ERROR or NOT ON SIZE ERROR."),
    ("add_giving", "ADD operands GIVING giving; ADD a TO b GIVING c is add_giving([a, b], c)."),
    ("subtract", "SUBTRACT operands FROM targets. Arguments and result as for add."),
    ("subtract_giving", "SUBTRACT operands FROM minuend GIVING giving."),
    ("multiply", "MULTIPLY operand BY targets."),
    ("multiply_giving", "MULTIPLY a BY b GIVING giving."),
    ("divide_into", "DIVIDE divisor INTO targets."),
    ("divide_giving", "DIVIDE dividend BY divisor GIVING giving (also DIVIDE divisor INTO "
     "dividend GIVING giving)."),
    ("divide_remainder", "DIVIDE dividend BY divisor GIVING quotient REMAINDER remainder."),
    ("compute", "COMPUTE targets = value. value is an expression of CobDecimal values, "
     "e.g. compute(x, dec(a) * dec(b) / 100 - dec(c), rounded=True); +, -, *, / and unary "
     "minus are available, written in the COBOL order of evaluation."),
    ("dec", "CobDecimal from a FieldRef, int, Decimal or numeric string, for compute "
     "expressions and comparisons."),
    ("CobDecimal", "Intermediate result of compute expressions. `to_decimal()` gives a "
     "Decimal."),
    ("display_line", "The bytes DISPLAY item ... writes, newline included. Items: FieldRefs "
     "and literals (str or bytes; a numeric literal is passed as its text, e.g. \"12\")."),
    ("display_bytes", "The bytes DISPLAY writes for one item, without newline."),
    ("string", "STRING ... INTO into [WITH POINTER pointer]. parts: list of (source, "
     "delimiter); delimiter None means DELIMITED BY SIZE. Returns True on overflow."),
    ("unstring", "UNSTRING source [DELIMITED BY ...] INTO targets [WITH POINTER pointer] "
     "[TALLYING IN tallying]. delimiters: list of str, bytes or FieldRef, or (delimiter, True) "
     "for ALL delimiter; an empty list means no DELIMITED BY. targets: FieldRef or Into. "
     "Returns True on overflow."),
    ("Into", "One UNSTRING receiver with optional DELIMITER IN and COUNT IN items."),
    ("Phrase", "One INSPECT phrase. mode: \"ALL\", \"LEADING\", \"FIRST\" (REPLACING only) or "
     "\"CHARACTERS\"; pattern: searched text; by: replacement (REPLACING); counter: FieldRef "
     "(TALLYING); before / after: INITIAL delimiters."),
    ("inspect_tallying", "INSPECT field TALLYING with a list of Phrase (each with counter)."),
    ("inspect_replacing", "INSPECT field REPLACING with a list of Phrase (each with by)."),
    ("inspect_converting", "INSPECT field CONVERTING from_chars TO to_chars [BEFORE|AFTER "
     "INITIAL x]."),
    ("Stdin", "Standard input for ACCEPT: inp = Stdin(stdin_bytes); inp.accept(ref) is "
     "ACCEPT ref."),
    ("accept_line", "Store one input line (without newline) into ref as ACCEPT does."),
    ("SPACES", "Figurative constant SPACE / SPACES."),
    ("ZEROS", "Figurative constant ZERO / ZEROS / ZEROES."),
    ("HIGH_VALUES", "Figurative constant HIGH-VALUE / HIGH-VALUES."),
    ("LOW_VALUES", "Figurative constant LOW-VALUE / LOW-VALUES."),
    ("All", "ALL \"literal\" as a sender."),
    ("DISPLAY", "USAGE DISPLAY."),
    ("COMP", "USAGE COMP / BINARY."),
    ("COMP3", "USAGE COMP-3 / PACKED-DECIMAL."),
    ("COMP5", "USAGE COMP-5."),
    ("Unsupported", "Raised for a construct or data case outside the modelled subset."),
    ("MoveError", "Raised for a MOVE outside the modelled subset."),
    ("PicError", "Raised for a PICTURE outside the modelled subset."),
    ("DataError", "Raised when an item holds bytes that are not valid for its USAGE."),
]
FILES = [
    ("LineSequentialReader", "LINE SEQUENTIAL input file: LineSequentialReader(data, record_size)."
     " read(into) reads the next record into the FieldRef `into` and returns its bytes, or "
     "returns None at end of file."),
    ("LineSequentialWriter", "LINE SEQUENTIAL output file. write(record) with a FieldRef or "
     "bytes; getvalue() returns the file contents."),
    ("RecordSequentialReader", "ORGANIZATION SEQUENTIAL (fixed-length records) input file; "
     "read as for LineSequentialReader."),
    ("RecordSequentialWriter", "ORGANIZATION SEQUENTIAL output file; write and getvalue as for "
     "LineSequentialWriter."),
]
NO_SIGNATURE = {"FieldRef", "CobDecimal"}  # constructed by Storage, not by translations
NOT_LISTED = {"edit", "store_numeric", "store_cobdec", "Pic", "parse_pic"}  # internal helpers


def _signature(obj) -> str:
    if not callable(obj):
        return ""
    try:
        return str(inspect.signature(obj)).replace("'", "")
    except (TypeError, ValueError):
        return ""


def generate() -> str:
    from .. import runtime
    from ..runtime import files

    listed = {n for n, _ in ENTRIES}
    missing = set(runtime.__all__) - listed - NOT_LISTED
    if missing:
        raise SystemExit(f"public names without a reviewed entry: {sorted(missing)}")
    parts = ["# API reference: cobol_equiv.runtime\n", INTRO]
    for name, doc in ENTRIES:
        obj = getattr(runtime, name)
        sig = "" if name in NO_SIGNATURE or inspect.isclass(obj) and issubclass(obj, Exception) \
            else _signature(obj)
        parts.append(f"### {name}{sig}\n\n{doc}\n")
    parts.append("## cobol_equiv.runtime.files\n")
    for name, doc in FILES:
        parts.append(f"### {name}{_signature(getattr(files, name))}\n\n{doc}\n")
    return "\n".join(parts)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    text = generate()
    if a.check:
        if SHEET.read_text(encoding="utf-8") != text:
            print(f"{SHEET} differs from the generated sheet")
            return 1
        return 0
    SHEET.parent.mkdir(parents=True, exist_ok=True)
    SHEET.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

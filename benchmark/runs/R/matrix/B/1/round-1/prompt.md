Translate the COBOL program below into a Python module.

The module must behave exactly like the program compiled with GnuCOBOL 3.1.2
(cobc -x -std=default): for every input whose records fit the program's
record descriptions, it must produce byte for byte the same standard output
and output files.

Use the Python package cobol_equiv.runtime, documented in the API reference
below, for COBOL data and statements. Besides it, use only the Python
standard library.

## IO contract
The Python module must define

    def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]

- stdin: everything the program reads with ACCEPT (one ACCEPT reads one line).
- input_files: for every file the program reads, the name in its ASSIGN
  clause mapped to the full content of the file. LINE SEQUENTIAL files are
  lines that end with "\n"; SEQUENTIAL files are fixed-length records
  without separators.
- The return value is all bytes the program writes to standard output, and
  a dict that maps the ASSIGN name of every file the program opens for
  output to the full content of that file.
- The module must not read the clock, random sources, the network or the
  file system, and must not start processes. It runs on Python 3.12.

## Examples
These are inputs and the exact outputs of the COBOL program.
### Example 1
stdin = b''
input_files = {'CELLS.DAT': b'00=00p\n'}
expected stdout = b'    0     0     0     0     0           =     0\n    0     0     0     0     0           =     0\n    0     0     0     0     0           =     0\n    0     0     0     0     0           =     0\nCOL 1     0\nCOL 2     0\nCOL 3     0\nCOL 4     0\nCOL 5     0\nMAX +0000 AT 1,1 BAD 01\n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'CELLS.DAT': b'30=00p\n'}
expected stdout = b'    0     0     0     0     0           =     0\n    0     0     0     0     0           =     0\n    0     0     0     0     0           =     0\n    0     0     0     0     0           =     0\nCOL 1     0\nCOL 2     0\nCOL 3     0\nCOL 4     0\nCOL 5     0\nMAX +0000 AT 1,1 BAD 01\n'
expected output_files = {}

## API reference: cobol_equiv.runtime
# API reference: cobol_equiv.runtime

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

### Storage(name: str, items: list[Item], area: bytearray | None = None)

A record or WORKING-STORAGE area. `items`: list of Item from Num, Alnum, Edited, Filler, Group. Without `area` the storage is initialised as COBOL does (VALUE clauses applied). `st[name]` returns the FieldRef of a data name (first occurrence); `st.f(name, *subs)` the FieldRef of a subscripted item; `st.record()` the whole area as one FieldRef (for READ ... INTO it). Data names must be unique within one Storage.

### Group(name, children, occurs=None, redefines=None) -> Item

Group item. `children`: list of Item. `occurs`: OCCURS n. `redefines`: name of an earlier sibling.

### Num(name, pic, usage='DISPLAY', value=None, occurs=None, redefines=None) -> Item

Numeric item, e.g. Num("BAL", "S9(5)V99", usage=COMP3, value="0"). usage: DISPLAY (default), COMP, COMP3, COMP5. value: VALUE clause (number, numeric string or figurative constant).

### Alnum(name, pic, value=None, occurs=None, redefines=None) -> Item

Alphanumeric (PIC X) or alphabetic (PIC A) item.

### Edited(name, pic, value=None, occurs=None, redefines=None) -> Item

Numeric-edited item, e.g. Edited("OUT", "ZZ,ZZ9.99-").

### Filler(pic, value=None) -> Item

Unnamed item (FILLER), e.g. Filler("X(3)", " - ").

### FieldRef

One item at a position in a storage area. Properties: `raw` (bytes), `text` (str, latin-1), `value` (Decimal, numeric items only), `pic`, `usage`, `category`. `set_raw(bytes)` replaces the bytes (same length). `int(ref)` gives the integer value.

### refmod(f: FieldRef, start: int, length: int | None = None) -> FieldRef

Reference modification: refmod(ref, start, length) is `ref (start:length)`, refmod(ref, start) is `ref (start:)`. The result is an alphanumeric FieldRef sharing the item's storage, usable as sender or receiver.

### move(src, *dsts: FieldRef) -> None

MOVE src TO each of dsts. src: a FieldRef, an alphanumeric literal (str or bytes), a numeric literal (int or Decimal) or a figurative constant (SPACES, ZEROS, HIGH_VALUES, LOW_VALUES, All("x")).

### initialize(f: FieldRef) -> None

INITIALIZE f (no REPLACING phrase).

### add(operands, targets, *, rounded=False, on_size_error=False) -> bool

ADD operands TO targets. operands: one operand or a list. targets: a FieldRef, (FieldRef, rounded) or a list of these. Returns True if a size error occurred; pass on_size_error=True when the statement has ON SIZE ERROR or NOT ON SIZE ERROR.

### add_giving(operands, giving, *, rounded=False, on_size_error=False) -> bool

ADD operands GIVING giving; ADD a TO b GIVING c is add_giving([a, b], c).

### subtract(operands, targets, *, rounded=False, on_size_error=False) -> bool

SUBTRACT operands FROM targets. Arguments and result as for add.

### subtract_giving(operands, minuend, giving, *, rounded=False, on_size_error=False) -> bool

SUBTRACT operands FROM minuend GIVING giving.

### multiply(operand, targets, *, rounded=False, on_size_error=False) -> bool

MULTIPLY operand BY targets.

### multiply_giving(a, b, giving, *, rounded=False, on_size_error=False) -> bool

MULTIPLY a BY b GIVING giving.

### divide_into(divisor, targets, *, rounded=False, on_size_error=False) -> bool

DIVIDE divisor INTO targets.

### divide_giving(dividend, divisor, giving, *, rounded=False, on_size_error=False) -> bool

DIVIDE dividend BY divisor GIVING giving (also DIVIDE divisor INTO dividend GIVING giving).

### divide_remainder(dividend, divisor, quotient: FieldRef, remainder: FieldRef, *, rounded=False, on_size_error=False) -> bool

DIVIDE dividend BY divisor GIVING quotient REMAINDER remainder.

### compute(targets, value, *, rounded=False, on_size_error=False) -> bool

COMPUTE targets = value. value is an expression of CobDecimal values, e.g. compute(x, dec(a) * dec(b) / 100 - dec(c), rounded=True); +, -, *, / and unary minus are available, written in the COBOL order of evaluation.

### dec(x) -> CobDecimal

CobDecimal from a FieldRef, int, Decimal or numeric string, for compute expressions and comparisons.

### CobDecimal

Intermediate result of compute expressions. `to_decimal()` gives a Decimal.

### display_line(*items) -> bytes

The bytes DISPLAY item ... writes, newline included. Items: FieldRefs and literals (str or bytes; a numeric literal is passed as its text, e.g. "12").

### display_bytes(item) -> bytes

The bytes DISPLAY writes for one item, without newline.

### string(parts, into: FieldRef, pointer: FieldRef | None = None) -> bool

STRING ... INTO into [WITH POINTER pointer]. parts: list of (source, delimiter); delimiter None means DELIMITED BY SIZE. Returns True on overflow.

### unstring(source, delimiters, targets, pointer: FieldRef | None = None, tallying: FieldRef | None = None) -> bool

UNSTRING source [DELIMITED BY ...] INTO targets [WITH POINTER pointer] [TALLYING IN tallying]. delimiters: list of str, bytes or FieldRef, or (delimiter, True) for ALL delimiter; an empty list means no DELIMITED BY. targets: FieldRef or Into. Returns True on overflow.

### Into(field: FieldRef, delimiter_in: FieldRef | None = None, count_in: FieldRef | None = None) -> None

One UNSTRING receiver with optional DELIMITER IN and COUNT IN items.

### Phrase(mode: str, pattern: object = None, by: object = None, counter: FieldRef | None = None, before: object = None, after: object = None) -> None

One INSPECT phrase. mode: "ALL", "LEADING", "FIRST" (REPLACING only) or "CHARACTERS"; pattern: searched text; by: replacement (REPLACING); counter: FieldRef (TALLYING); before / after: INITIAL delimiters.

### inspect_tallying(field, phrases: list[Phrase]) -> None

INSPECT field TALLYING with a list of Phrase (each with counter).

### inspect_replacing(field: FieldRef, phrases: list[Phrase]) -> None

INSPECT field REPLACING with a list of Phrase (each with by).

### inspect_converting(field: FieldRef, from_chars, to_chars, before=None, after=None) -> None

INSPECT field CONVERTING from_chars TO to_chars [BEFORE|AFTER INITIAL x].

### Stdin(data: bytes)

Standard input for ACCEPT: inp = Stdin(stdin_bytes); inp.accept(ref) is ACCEPT ref.

### accept_line(line: bytes, ref: FieldRef) -> None

Store one input line (without newline) into ref as ACCEPT does.

### SPACES

Figurative constant SPACE / SPACES.

### ZEROS

Figurative constant ZERO / ZEROS / ZEROES.

### HIGH_VALUES

Figurative constant HIGH-VALUE / HIGH-VALUES.

### LOW_VALUES

Figurative constant LOW-VALUE / LOW-VALUES.

### All(lit: str | bytes)

ALL "literal" as a sender.

### DISPLAY

USAGE DISPLAY.

### COMP

USAGE COMP / BINARY.

### COMP3

USAGE COMP-3 / PACKED-DECIMAL.

### COMP5

USAGE COMP-5.

### Unsupported

Raised for a construct or data case outside the modelled subset.

### MoveError

Raised for a MOVE outside the modelled subset.

### PicError

Raised for a PICTURE outside the modelled subset.

### DataError

Raised when an item holds bytes that are not valid for its USAGE.

## cobol_equiv.runtime.files

### LineSequentialReader(data: bytes, record_size: int, long_lines: str = 'truncate')

LINE SEQUENTIAL input file: LineSequentialReader(data, record_size), record_size being the record length in bytes; leave long_lines at its default. read(into) reads the next record into the FieldRef `into` and returns its bytes, or returns None at end of file.

### LineSequentialWriter()

LINE SEQUENTIAL output file. write(record) with a FieldRef or bytes; getvalue() returns the file contents.

### RecordSequentialReader(data: bytes, record_size: int)

ORGANIZATION SEQUENTIAL (fixed-length records) input file; read as for LineSequentialReader.

### RecordSequentialWriter()

ORGANIZATION SEQUENTIAL output file; write and getvalue as for LineSequentialWriter.

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. MATRIX.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CELL-FILE ASSIGN TO "CELLS.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD CELL-FILE.
       01 CELL-REC.
          05 CL-ROW         PIC 9.
          05 CL-COL         PIC 9.
          05 CL-OP          PIC X.
          05 CL-VAL         PIC S9(3).
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-MATRIX.
          05 WS-ROW OCCURS 4 TIMES.
             10 WS-CELL     PIC S9(4) OCCURS 5 TIMES.
       01 WS-TRANS.
          05 WT-ROW OCCURS 5 TIMES.
             10 WT-CELL     PIC S9(4) OCCURS 4 TIMES.
       01 WS-I              PIC 9.
       01 WS-J              PIC 9.
       01 WS-SUM            PIC S9(5).
       01 WS-MAX            PIC S9(4).
       01 WS-MAX-I          PIC 9.
       01 WS-MAX-J          PIC 9.
       01 WS-BAD            PIC 99 VALUE 0.
       01 WS-LINE           PIC X(40).
       01 WS-PTR            PIC 99.
       01 WS-ED             PIC -(4)9.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT CELL-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ CELL-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM APPLY-CELL
               END-READ
           END-PERFORM
           CLOSE CELL-FILE
           PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > 4
                   AFTER WS-J FROM 1 BY 1 UNTIL WS-J > 5
               MOVE WS-CELL (WS-I WS-J) TO WT-CELL (WS-J WS-I)
           END-PERFORM
           MOVE WS-CELL (1 1) TO WS-MAX
           MOVE 1 TO WS-MAX-I WS-MAX-J
           PERFORM PRINT-ROW VARYING WS-I FROM 1 BY 1 UNTIL WS-I > 4
           PERFORM VARYING WS-J FROM 1 BY 1 UNTIL WS-J > 5
               MOVE 0 TO WS-SUM
               PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > 4
                   ADD WT-CELL (WS-J WS-I) TO WS-SUM
               END-PERFORM
               MOVE WS-SUM TO WS-ED
               DISPLAY "COL " WS-J " " WS-ED
           END-PERFORM
           DISPLAY "MAX " WS-MAX " AT " WS-MAX-I "," WS-MAX-J
               " BAD " WS-BAD
           STOP RUN.

       APPLY-CELL.
           IF CL-ROW < 1 OR CL-ROW > 4 OR CL-COL < 1 OR CL-COL > 5
               ADD 1 TO WS-BAD
           ELSE
               EVALUATE CL-OP
                   WHEN "="
                       MOVE CL-VAL TO WS-CELL (CL-ROW CL-COL)
                   WHEN "+"
                       ADD CL-VAL TO WS-CELL (CL-ROW CL-COL)
                   WHEN "*"
                       MULTIPLY CL-VAL BY WS-CELL (CL-ROW CL-COL)
                   WHEN OTHER
                       ADD 1 TO WS-BAD
               END-EVALUATE
           END-IF.

       PRINT-ROW.
           MOVE SPACES TO WS-LINE
           MOVE 1 TO WS-PTR
           MOVE 0 TO WS-SUM
           PERFORM VARYING WS-J FROM 1 BY 1 UNTIL WS-J > 5
               PERFORM CHECK-MAX
               ADD WS-CELL (WS-I WS-J) TO WS-SUM
               MOVE WS-CELL (WS-I WS-J) TO WS-ED
               STRING WS-ED DELIMITED BY SIZE
                   " " DELIMITED BY SIZE
                   INTO WS-LINE WITH POINTER WS-PTR
           END-PERFORM
           MOVE WS-SUM TO WS-ED
           DISPLAY WS-LINE "= " WS-ED.

       CHECK-MAX.
           IF WS-CELL (WS-I WS-J) > WS-MAX
               MOVE WS-CELL (WS-I WS-J) TO WS-MAX
               MOVE WS-I TO WS-MAX-I
               MOVE WS-J TO WS-MAX-J
           END-IF.
```

## Your previous translation
```python
from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited, move, add, multiply, dec,
    display_line, string, SPACES,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = []

    rec = Storage("CELL-REC", [
        Num("CL-ROW", "9"),
        Num("CL-COL", "9"),
        Alnum("CL-OP", "X"),
        Num("CL-VAL", "S9(3)"),
    ])

    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
        Group("WS-MATRIX", [
            Group("WS-ROW", [
                Num("WS-CELL", "S9(4)", occurs=5),
            ], occurs=4),
        ]),
        Group("WS-TRANS", [
            Group("WT-ROW", [
                Num("WT-CELL", "S9(4)", occurs=4),
            ], occurs=5),
        ]),
        Num("WS-I", "9"),
        Num("WS-J", "9"),
        Num("WS-SUM", "S9(5)"),
        Num("WS-MAX", "S9(4)"),
        Num("WS-MAX-I", "9"),
        Num("WS-MAX-J", "9"),
        Num("WS-BAD", "99", value=0),
        Alnum("WS-LINE", "X(40)"),
        Num("WS-PTR", "99"),
        Edited("WS-ED", "-(4)9"),
    ])

    def cell(i, j):
        return ws.f("WS-CELL", i, j)

    def apply_cell():
        r = dec(rec["CL-ROW"])
        c = dec(rec["CL-COL"])
        if r < dec(1) or r > dec(4) or c < dec(1) or c > dec(5):
            add(1, ws["WS-BAD"])
        else:
            op = rec["CL-OP"].text
            ri = int(rec["CL-ROW"])
            ci = int(rec["CL-COL"])
            if op == "=":
                move(rec["CL-VAL"], cell(ri, ci))
            elif op == "+":
                add(rec["CL-VAL"], cell(ri, ci))
            elif op == "*":
                multiply(rec["CL-VAL"], cell(ri, ci))
            else:
                add(1, ws["WS-BAD"])

    def check_max():
        i = int(ws["WS-I"])
        j = int(ws["WS-J"])
        if dec(cell(i, j)) > dec(ws["WS-MAX"]):
            move(cell(i, j), ws["WS-MAX"])
            move(ws["WS-I"], ws["WS-MAX-I"])
            move(ws["WS-J"], ws["WS-MAX-J"])

    def print_row():
        move(SPACES, ws["WS-LINE"])
        move(1, ws["WS-PTR"])
        move(0, ws["WS-SUM"])
        move(1, ws["WS-J"])
        while not int(ws["WS-J"]) > 5:
            check_max()
            i = int(ws["WS-I"])
            j = int(ws["WS-J"])
            add(cell(i, j), ws["WS-SUM"])
            move(cell(i, j), ws["WS-ED"])
            string([(ws["WS-ED"], None), (" ", None)], ws["WS-LINE"], pointer=ws["WS-PTR"])
            add(1, ws["WS-J"])
        move(ws["WS-SUM"], ws["WS-ED"])
        out.append(display_line(ws["WS-LINE"], "= ", ws["WS-ED"]))

    reader = LineSequentialReader(input_files.get("CELLS.DAT", b""), 6)
    while ws["WS-EOF"].text != "Y":
        if reader.read(rec.record()) is None:
            move("Y", ws["WS-EOF"])
        else:
            apply_cell()

    move(1, ws["WS-I"])
    while not int(ws["WS-I"]) > 4:
        move(1, ws["WS-J"])
        while not int(ws["WS-J"]) > 5:
            i = int(ws["WS-I"])
            j = int(ws["WS-J"])
            move(cell(i, j), ws.f("WT-CELL", j, i))
            add(1, ws["WS-J"])
        add(1, ws["WS-I"])

    move(cell(1, 1), ws["WS-MAX"])
    move(1, ws["WS-MAX-I"], ws["WS-MAX-J"])

    move(1, ws["WS-I"])
    while not int(ws["WS-I"]) > 4:
        print_row()
        add(1, ws["WS-I"])

    move(1, ws["WS-J"])
    while not int(ws["WS-J"]) > 5:
        move(0, ws["WS-SUM"])
        move(1, ws["WS-I"])
        while not int(ws["WS-I"]) > 4:
            add(ws.f("WT-CELL", int(ws["WS-J"]), int(ws["WS-I"])), ws["WS-SUM"])
            add(1, ws["WS-I"])
        move(ws["WS-SUM"], ws["WS-ED"])
        out.append(display_line("COL ", ws["WS-J"], " ", ws["WS-ED"]))
        add(1, ws["WS-J"])

    out.append(display_line("MAX ", ws["WS-MAX"], " AT ", ws["WS-MAX-I"], ",",
                            ws["WS-MAX-J"], " BAD ", ws["WS-BAD"]))

    return b"".join(out), {}
```

## Test result
The previous translation was run on a test input that is not one of the
examples above.
stdin = b''
input_files = {'CELLS.DAT': b''}
The translation raised TypeError: '>' not supported between instances of 'CobDecimal' and 'CobDecimal'

Fix the translation. Reply with the complete corrected Python module in one
```python code block. Do not write anything after the code block.

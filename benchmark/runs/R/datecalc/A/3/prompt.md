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
input_files = {'DATES.DAT': b'2000010120000101000000\n'}
expected stdout = b'20000101 20000101        0 SAT 20000101\n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'DATES.DAT': b'2026130102097152631447\n'}
expected stdout = b'20261301 INVALID FROM DATE\n'
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
       PROGRAM-ID. DATECALC.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT DATE-FILE ASSIGN TO "DATES.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD DATE-FILE.
       01 DATE-REC.
          05 DT-FROM        PIC 9(8).
          05 DT-TO          PIC 9(8).
          05 DT-OFFSET      PIC S9(6).
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-CUM-TEXT       PIC X(36)
                  VALUE "000031059090120151181212243273304334".
       01 WS-CUM-TABLE REDEFINES WS-CUM-TEXT.
          05 WS-CUM         PIC 999 OCCURS 12.
       01 WS-DIM-TEXT       PIC X(24)
                  VALUE "312831303130313130313031".
       01 WS-DIM-TABLE REDEFINES WS-DIM-TEXT.
          05 WS-DIM         PIC 99 OCCURS 12.
       01 WS-DOW-TEXT       PIC X(21)
                  VALUE "MONTUEWEDTHUFRISATSUN".
       01 WS-DOW-TABLE REDEFINES WS-DOW-TEXT.
          05 WS-DOW-NAME    PIC X(3) OCCURS 7.
       01 WS-DATE           PIC 9(8).
       01 WS-DATE-R REDEFINES WS-DATE.
          05 WS-YYYY        PIC 9(4).
          05 WS-MM          PIC 99.
          05 WS-DD          PIC 99.
       01 WS-VALID          PIC X.
       01 WS-LEAP           PIC X.
       01 WS-Q              PIC 9(7).
       01 WS-R4             PIC 9(4).
       01 WS-R100           PIC 9(4).
       01 WS-R400           PIC 9(4).
       01 WS-Y              PIC 9(5).
       01 WS-DAYNUM         PIC S9(8).
       01 WS-FROM-NUM       PIC S9(8).
       01 WS-TO-NUM         PIC S9(8).
       01 WS-NEW-NUM        PIC S9(8).
       01 WS-DIFF           PIC S9(8).
       01 WS-DIFF-ED        PIC -(7)9.
       01 WS-DOW-IX         PIC 9.
       01 WS-REM7           PIC 9.
       01 WS-MAXDAY         PIC 99.
       01 WS-RESULT         PIC X(8).
       01 WS-TRY            PIC S9(8).
       01 WS-DONE           PIC X.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT DATE-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ DATE-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM DO-PAIR
               END-READ
           END-PERFORM
           CLOSE DATE-FILE
           STOP RUN.

       DO-PAIR.
           MOVE DT-FROM TO WS-DATE
           PERFORM VALIDATE-DATE
           IF WS-VALID = "N"
               DISPLAY DT-FROM " INVALID FROM DATE"
               EXIT PARAGRAPH
           END-IF
           PERFORM DATE-TO-NUM
           MOVE WS-DAYNUM TO WS-FROM-NUM
           MOVE DT-TO TO WS-DATE
           PERFORM VALIDATE-DATE
           IF WS-VALID = "N"
               DISPLAY DT-TO " INVALID TO DATE"
               EXIT PARAGRAPH
           END-IF
           PERFORM DATE-TO-NUM
           MOVE WS-DAYNUM TO WS-TO-NUM
           COMPUTE WS-DIFF = WS-TO-NUM - WS-FROM-NUM
           MOVE WS-DIFF TO WS-DIFF-ED
           DIVIDE WS-FROM-NUM BY 7 GIVING WS-Q REMAINDER WS-REM7
           COMPUTE WS-DOW-IX = WS-REM7 + 1
           COMPUTE WS-NEW-NUM = WS-FROM-NUM + DT-OFFSET
           IF WS-NEW-NUM < 0 OR WS-NEW-NUM > 3067670
               MOVE "RANGE" TO WS-RESULT
           ELSE
               MOVE WS-NEW-NUM TO WS-DAYNUM
               PERFORM NUM-TO-DATE
               MOVE WS-DATE TO WS-RESULT
           END-IF
           DISPLAY DT-FROM " " DT-TO " " WS-DIFF-ED " "
                   WS-DOW-NAME (WS-DOW-IX) " " WS-RESULT.

       VALIDATE-DATE.
           MOVE "Y" TO WS-VALID
           IF WS-YYYY < 1601 OR WS-MM < 1 OR WS-MM > 12 OR WS-DD < 1
               MOVE "N" TO WS-VALID
           ELSE
               PERFORM CHECK-LEAP
               MOVE WS-DIM (WS-MM) TO WS-MAXDAY
               IF WS-MM = 2 AND WS-LEAP = "Y"
                   ADD 1 TO WS-MAXDAY
               END-IF
               IF WS-DD > WS-MAXDAY
                   MOVE "N" TO WS-VALID
               END-IF
           END-IF.

       CHECK-LEAP.
           DIVIDE WS-YYYY BY 4 GIVING WS-Q REMAINDER WS-R4
           DIVIDE WS-YYYY BY 100 GIVING WS-Q REMAINDER WS-R100
           DIVIDE WS-YYYY BY 400 GIVING WS-Q REMAINDER WS-R400
           IF WS-R4 = 0 AND (WS-R100 NOT = 0 OR WS-R400 = 0)
               MOVE "Y" TO WS-LEAP
           ELSE
               MOVE "N" TO WS-LEAP
           END-IF.

       DATE-TO-NUM.
           COMPUTE WS-Y = WS-YYYY - 1601
           DIVIDE WS-Y BY 4 GIVING WS-Q
           COMPUTE WS-DAYNUM = WS-Y * 365 + WS-Q
           DIVIDE WS-Y BY 100 GIVING WS-Q
           SUBTRACT WS-Q FROM WS-DAYNUM
           DIVIDE WS-Y BY 400 GIVING WS-Q
           ADD WS-Q TO WS-DAYNUM
           ADD WS-CUM (WS-MM) WS-DD TO WS-DAYNUM
           SUBTRACT 1 FROM WS-DAYNUM
           PERFORM CHECK-LEAP
           IF WS-LEAP = "Y" AND WS-MM > 2
               ADD 1 TO WS-DAYNUM
           END-IF.

       NUM-TO-DATE.
           MOVE WS-DAYNUM TO WS-TRY
           DIVIDE WS-DAYNUM BY 366 GIVING WS-Y
           COMPUTE WS-YYYY = WS-Y + 1601
           MOVE 1 TO WS-MM WS-DD
           MOVE "N" TO WS-DONE
           PERFORM UNTIL WS-DONE = "Y"
               IF WS-YYYY = 9999
                   MOVE "Y" TO WS-DONE
               ELSE
                   ADD 1 TO WS-YYYY
                   PERFORM DATE-TO-NUM
                   IF WS-DAYNUM > WS-TRY
                       SUBTRACT 1 FROM WS-YYYY
                       MOVE "Y" TO WS-DONE
                   END-IF
               END-IF
           END-PERFORM
           MOVE 12 TO WS-MM
           PERFORM DATE-TO-NUM
           PERFORM UNTIL WS-DAYNUM <= WS-TRY
               SUBTRACT 1 FROM WS-MM
               PERFORM DATE-TO-NUM
           END-PERFORM
           COMPUTE WS-DD = WS-TRY - WS-DAYNUM + 1.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.

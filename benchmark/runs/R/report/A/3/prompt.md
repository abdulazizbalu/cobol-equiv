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
input_files = {'AMOUNTS.DAT': b'      00000000p000000000p\n'}
expected stdout = b''
expected output_files = {'REPORT.DAT': b'             0.00           $0.00   **********0.00 +   0 00/00/00       0\n           0.000 000 000 $     0.00     0.0+\nTOTAL            $0.00   QTY       0\n'}

### Example 2
stdin = b''
input_files = {'AMOUNTS.DAT': b'4N/VY 4999999990003420001\n'}
expected stdout = b''
expected output_files = {'REPORT.DAT': b'4N/VY  999,999.99   $4,999,999.99   **4,999,999.99 +   1 00/03/42       1\n       99999.990 000 342 $99,999.99   999.9+    1\nTOTAL    $4,999,999.99   QTY       1\n'}

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
       PROGRAM-ID. REPORT1.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT AMT-FILE ASSIGN TO "AMOUNTS.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
           SELECT RPT-FILE ASSIGN TO "REPORT.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD AMT-FILE.
       01 AMT-REC.
          05 AM-LABEL       PIC X(6).
          05 AM-VALUE       PIC S9(7)V99.
          05 AM-DATE        PIC 9(6).
          05 AM-QTY         PIC S9(4).
       FD RPT-FILE.
       01 RPT-REC           PIC X(80).
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-TOTAL          PIC S9(9)V99 VALUE 0.
       01 WS-QTY-TOTAL      PIC S9(6) VALUE 0.
       01 LINE-1.
          05 L1-LABEL       PIC X(6).
          05 FILLER         PIC X VALUE SPACE.
          05 L1-A           PIC ZZZ,ZZ9.99-.
          05 FILLER         PIC X VALUE SPACE.
          05 L1-B           PIC $$$,$$$,$$9.99CR.
          05 FILLER         PIC X VALUE SPACE.
          05 L1-C           PIC ***,***,**9.99.
          05 FILLER         PIC X VALUE SPACE.
          05 L1-D           PIC +ZZZ9.
          05 FILLER         PIC X VALUE SPACE.
          05 L1-E           PIC 99/99/99.
          05 FILLER         PIC X VALUE SPACE.
          05 L1-F           PIC ---,--9.
       01 LINE-2.
          05 FILLER         PIC X(7) VALUE "       ".
          05 L2-G           PIC Z(4)9.999.
          05 FILLER         PIC X VALUE SPACE.
          05 L2-H           PIC 999B999.
          05 FILLER         PIC X VALUE SPACE.
          05 L2-I           PIC $ZZ,ZZ9.99DB.
          05 FILLER         PIC X VALUE SPACE.
          05 L2-J           PIC ZZ9.9+.
          05 FILLER         PIC X VALUE SPACE.
          05 L2-K           PIC ZZZZ.
       01 TOTAL-LINE.
          05 FILLER         PIC X(7) VALUE "TOTAL  ".
          05 TL-AMOUNT      PIC $$$$,$$$,$$9.99CR.
          05 FILLER         PIC X(5) VALUE " QTY ".
          05 TL-QTY         PIC ---,--9.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT AMT-FILE OUTPUT RPT-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ AMT-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM REPORT-ONE
               END-READ
           END-PERFORM
           MOVE WS-TOTAL TO TL-AMOUNT
           MOVE WS-QTY-TOTAL TO TL-QTY
           WRITE RPT-REC FROM TOTAL-LINE
           CLOSE AMT-FILE RPT-FILE
           STOP RUN.

       REPORT-ONE.
           MOVE AM-LABEL TO L1-LABEL
           MOVE AM-VALUE TO L1-A L1-B L1-C L2-G L2-I L2-J
           MOVE AM-QTY TO L1-D L1-F L2-K
           MOVE AM-DATE TO L1-E L2-H
           WRITE RPT-REC FROM LINE-1
           WRITE RPT-REC FROM LINE-2
           ADD AM-VALUE TO WS-TOTAL
           ADD AM-QTY TO WS-QTY-TOTAL.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.

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
input_files = {'CUST.DAT': b'00000                  0000                      00000000000000p\n'}
expected stdout = b'NO LAST NAME 00000 [                    ]\nCOUNT 001 TOTAL        0.00\n'
expected output_files = {'CUSTLIST.DAT': b'    0|                   |          ,   0             |00/00/0000|     0.00 BADM\n'}

### Example 2
stdin = b''
input_files = {'CUST.DAT': b'00729g+GCac=r  .*/dL<Mo0649                      74911298000010p\n00315353       O{f=IBJ 9998$4          hmu3)30Wxl000102990065536\n99998~y:|y*NeFcvd `95jW999989          Ws>m      000304050165583\n'}
expected stdout = b'COUNT 003 TOTAL     2310.19\n'
expected output_files = {'CUSTLIST.DAT': b'  729|.*/dL<Mo g+GCac=r  |          , 649             |98/12/7491|    -1.00\n  315|O{f=IBJ  353       |hmu3)30Wxl,9998 $4          |99/02/0001|   655.36 OLD\n99998|vd `95jW ~y:|y*NeFc|Ws>m      ,9999 89          |05/04/0003|  1655.83 OLD\n'}

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
       PROGRAM-ID. CUSTLIST.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUST-FILE ASSIGN TO "CUST.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
           SELECT LIST-FILE ASSIGN TO "CUSTLIST.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD CUST-FILE.
       01 CUST-REC.
          05 CU-ID             PIC 9(5).
          05 CU-NAME.
             10 CU-LAST        PIC X(10).
             10 CU-FIRST       PIC X(8).
          05 CU-ADDR.
             10 CU-STREET.
                15 CU-HOUSE    PIC 9(4).
                15 CU-ROAD     PIC X(12).
             10 CU-CITY        PIC X(10).
          05 CU-OPENED.
             10 CU-YYYY        PIC 9(4).
             10 CU-MM          PIC 99.
             10 CU-DD          PIC 99.
          05 CU-OPENED-N REDEFINES CU-OPENED PIC 9(8).
          05 CU-BAL            PIC S9(5)V99.
       FD LIST-FILE.
       01 LIST-REC             PIC X(80).
       WORKING-STORAGE SECTION.
       01 WS-EOF               PIC X VALUE "N".
       01 WS-COUNT             PIC 9(3) VALUE 0.
       01 WS-TOTAL             PIC S9(7)V99 VALUE 0.
       01 WS-OUT-TOTAL         PIC -(7)9.99.
       01 WS-NAME-COPY         PIC X(20).
       01 WS-OUT.
          05 CU-ID             PIC Z(4)9.
          05 FILLER            PIC X VALUE "|".
          05 CU-NAME.
             10 CU-FIRST       PIC X(8).
             10 FILLER         PIC X VALUE SPACE.
             10 CU-LAST        PIC X(10).
          05 FILLER            PIC X VALUE "|".
          05 CU-ADDR.
             10 CU-CITY        PIC X(10).
             10 FILLER         PIC X VALUE ",".
             10 CU-STREET.
                15 CU-HOUSE    PIC ZZZ9.
                15 FILLER      PIC X VALUE SPACE.
                15 CU-ROAD     PIC X(12).
          05 FILLER            PIC X VALUE "|".
          05 WO-DATE.
             10 WO-DD          PIC 99.
             10 FILLER         PIC X VALUE "/".
             10 WO-MM          PIC 99.
             10 FILLER         PIC X VALUE "/".
             10 WO-YYYY        PIC 9(4).
          05 FILLER            PIC X VALUE "|".
          05 CU-BAL            PIC -(5)9.99.
          05 WO-FLAG           PIC X(5).
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT CUST-FILE OUTPUT LIST-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ CUST-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM LIST-CUSTOMER
               END-READ
           END-PERFORM
           CLOSE CUST-FILE LIST-FILE
           MOVE WS-TOTAL TO WS-OUT-TOTAL
           DISPLAY "COUNT " WS-COUNT " TOTAL " WS-OUT-TOTAL
           STOP RUN.

       LIST-CUSTOMER.
           ADD 1 TO WS-COUNT
           ADD CU-BAL OF CUST-REC TO WS-TOTAL
           MOVE CORRESPONDING CUST-REC TO WS-OUT
           MOVE CU-DD TO WO-DD
           MOVE CU-MM TO WO-MM
           MOVE CU-YYYY TO WO-YYYY
           EVALUATE TRUE
               WHEN CU-MM < 1 OR CU-MM > 12
                   MOVE " BADM" TO WO-FLAG
               WHEN CU-OPENED-N < 19000101
                   MOVE " OLD" TO WO-FLAG
               WHEN OTHER
                   MOVE SPACES TO WO-FLAG
           END-EVALUATE
           WRITE LIST-REC FROM WS-OUT
           IF CU-LAST OF CUST-REC = SPACES
               MOVE CU-NAME OF CUST-REC TO WS-NAME-COPY
               DISPLAY "NO LAST NAME " CU-ID OF CUST-REC " ["
                   WS-NAME-COPY "]"
           END-IF.
```

## Your previous translation
```python
from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited, Filler,
    move, add, dec, display_line, SPACES,
)
from cobol_equiv.runtime.files import LineSequentialReader, LineSequentialWriter


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()

    cust = Storage("CUST-REC", [
        Group("CUST-REC", [
            Num("CU-ID", "9(5)"),
            Group("CU-NAME", [
                Alnum("CU-LAST", "X(10)"),
                Alnum("CU-FIRST", "X(8)"),
            ]),
            Group("CU-ADDR", [
                Group("CU-STREET", [
                    Num("CU-HOUSE", "9(4)"),
                    Alnum("CU-ROAD", "X(12)"),
                ]),
                Alnum("CU-CITY", "X(10)"),
            ]),
            Group("CU-OPENED", [
                Num("CU-YYYY", "9(4)"),
                Num("CU-MM", "99"),
                Num("CU-DD", "99"),
            ]),
            Num("CU-OPENED-N", "9(8)", redefines="CU-OPENED"),
            Num("CU-BAL", "S9(5)V99"),
        ]),
    ])

    lst = Storage("LIST-REC", [Alnum("LIST-REC", "X(80)")])

    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
        Num("WS-COUNT", "9(3)", value=0),
        Num("WS-TOTAL", "S9(7)V99", value=0),
        Edited("WS-OUT-TOTAL", "-(7)9.99"),
        Alnum("WS-NAME-COPY", "X(20)"),
    ])

    wo = Storage("WS-OUT", [
        Group("WS-OUT", [
            Edited("CU-ID", "Z(4)9"),
            Filler("X", "|"),
            Group("CU-NAME", [
                Alnum("CU-FIRST", "X(8)"),
                Filler("X", " "),
                Alnum("CU-LAST", "X(10)"),
            ]),
            Filler("X", "|"),
            Group("CU-ADDR", [
                Alnum("CU-CITY", "X(10)"),
                Filler("X", ","),
                Group("CU-STREET", [
                    Edited("CU-HOUSE", "ZZZ9"),
                    Filler("X", " "),
                    Alnum("CU-ROAD", "X(12)"),
                ]),
            ]),
            Filler("X", "|"),
            Group("WO-DATE", [
                Num("WO-DD", "99"),
                Filler("X", "/"),
                Num("WO-MM", "99"),
                Filler("X", "/"),
                Num("WO-YYYY", "9(4)"),
            ]),
            Filler("X", "|"),
            Edited("CU-BAL", "-(5)9.99"),
            Alnum("WO-FLAG", "X(5)"),
        ]),
    ])

    reader = LineSequentialReader(input_files.get("CUST.DAT", b""), 64)
    writer = LineSequentialWriter()

    def list_customer():
        add(1, ws["WS-COUNT"])
        add(cust["CU-BAL"], ws["WS-TOTAL"])
        # MOVE CORRESPONDING
        move(cust["CU-ID"], wo["CU-ID"])
        move(cust["CU-LAST"], wo["CU-LAST"])
        move(cust["CU-FIRST"], wo["CU-FIRST"])
        move(cust["CU-HOUSE"], wo["CU-HOUSE"])
        move(cust["CU-ROAD"], wo["CU-ROAD"])
        move(cust["CU-CITY"], wo["CU-CITY"])
        move(cust["CU-BAL"], wo["CU-BAL"])
        move(cust["CU-DD"], wo["WO-DD"])
        move(cust["CU-MM"], wo["WO-MM"])
        move(cust["CU-YYYY"], wo["WO-YYYY"])
        mm = dec(cust["CU-MM"])
        if mm < dec(1) or mm > dec(12):
            move(" BADM", wo["WO-FLAG"])
        elif dec(cust["CU-OPENED-N"]) < dec(19000101):
            move(" OLD", wo["WO-FLAG"])
        else:
            move(SPACES, wo["WO-FLAG"])
        move(wo["WS-OUT"], lst["LIST-REC"])
        writer.write(lst["LIST-REC"])
        if cust["CU-LAST"].raw == b" " * 10:
            move(cust["CU-NAME"], ws["WS-NAME-COPY"])
            out.extend(display_line("NO LAST NAME ", cust["CU-ID"], " [",
                                    ws["WS-NAME-COPY"], "]"))

    while ws["WS-EOF"].raw != b"Y":
        r = reader.read(cust.record())
        if r is None:
            move("Y", ws["WS-EOF"])
        else:
            list_customer()

    move(ws["WS-TOTAL"], ws["WS-OUT-TOTAL"])
    out.extend(display_line("COUNT ", ws["WS-COUNT"], " TOTAL ", ws["WS-OUT-TOTAL"]))
    return bytes(out), {"CUSTLIST.DAT": writer.getvalue()}
```

## Test result
The previous translation was run on a test input that is not one of the
examples above.
stdin = b''
input_files = {'CUST.DAT': b'00042Smith     John    0012Main St     Tashkent  20240315000123p\n99999          Ann     9999                      189912310000000\n00000X                 0000                      200013019999999\n'}
The translation raised TypeError: '<' not supported between instances of 'CobDecimal' and 'CobDecimal'

Fix the translation. Reply with the complete corrected Python module in one
```python code block. Do not write anything after the code block.

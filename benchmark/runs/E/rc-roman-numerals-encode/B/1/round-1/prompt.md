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
stdin = b'1\n'
input_files = {}
expected stdout = b'inp=0001 roman=I               \n'
expected output_files = {}

### Example 2
stdin = b'122\n1656\n'
input_files = {}
expected stdout = b'inp=0122 roman=CXXII           \ninp=1656 roman=MDCLVI          \n'
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
PROGRAM-ID. TOROMAN.
DATA DIVISION.
working-storage section.
  01 ws-number pic 9(4) value 0.
  01 ws-save-number pic 9(4).
  01 ws-tbl-def.
    03 filler pic x(7) value '1000M  '.
    03 filler pic x(7) value '0900CM '.
    03 filler pic x(7) value '0500D  '.
    03 filler pic x(7) value '0400CD '.
    03 filler pic x(7) value '0100C  '.
    03 filler pic x(7) value '0090XC '.
    03 filler pic x(7) value '0050L  '.
    03 filler pic x(7) value '0040XL '.
    03 filler pic x(7) value '0010X  '.
    03 filler pic x(7) value '0009IX '.
    03 filler pic x(7) value '0005V  '.
    03 filler pic x(7) value '0004IV '.
    03 filler pic x(7) value '0001I  '.
  01  filler redefines ws-tbl-def.
    03 filler occurs 13 times indexed by rx.
      05 ws-tbl-divisor    pic 9(4).
      05 ws-tbl-roman-ch   pic x(1) occurs 3 times indexed by cx.
  01 ocx pic 99.
  01 ws-roman.
    03 ws-roman-ch         pic x(1) occurs 16 times.
PROCEDURE DIVISION.
  accept ws-number
  perform
  until ws-number = 0
    move ws-number to ws-save-number
    if ws-number > 0 and ws-number < 4000
      initialize ws-roman
      move 0 to ocx
      perform varying rx from 1 by +1
      until ws-number = 0
        perform until ws-number < ws-tbl-divisor (rx)
          perform varying cx from 1 by +1
  		  until ws-tbl-roman-ch (rx, cx) = spaces
            compute ocx = ocx + 1
            move ws-tbl-roman-ch (rx, cx) to ws-roman-ch (ocx)
          end-perform
          compute ws-number = ws-number - ws-tbl-divisor (rx)
        end-perform
      end-perform
      display 'inp=' ws-save-number ' roman=' ws-roman
    else
      display 'inp=' ws-save-number ' invalid'
    end-if
    accept ws-number
  end-perform
  .
```

## Your previous translation
```python
from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Filler, move, compute, dec, initialize,
    display_line, Stdin,
)


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Num("WS-NUMBER", "9(4)", value=0),
        Num("WS-SAVE-NUMBER", "9(4)"),
        Group("WS-TBL-DEF", [
            Filler("X(7)", "1000M  "),
            Filler("X(7)", "0900CM "),
            Filler("X(7)", "0500D  "),
            Filler("X(7)", "0400CD "),
            Filler("X(7)", "0100C  "),
            Filler("X(7)", "0090XC "),
            Filler("X(7)", "0050L  "),
            Filler("X(7)", "0040XL "),
            Filler("X(7)", "0010X  "),
            Filler("X(7)", "0009IX "),
            Filler("X(7)", "0005V  "),
            Filler("X(7)", "0004IV "),
            Filler("X(7)", "0001I  "),
        ]),
        Group("WS-TBL-R", [
            Group("WS-TBL-ENT", [
                Num("WS-TBL-DIVISOR", "9(4)"),
                Alnum("WS-TBL-ROMAN-CH", "X(1)", occurs=3),
            ], occurs=13),
        ], redefines="WS-TBL-DEF"),
        Num("OCX", "99"),
        Group("WS-ROMAN", [
            Alnum("WS-ROMAN-CH", "X(1)", occurs=16),
        ]),
    ])

    out = bytearray()
    inp = Stdin(stdin)
    num = ws["WS-NUMBER"]
    save = ws["WS-SAVE-NUMBER"]
    ocx = ws["OCX"]
    roman = ws["WS-ROMAN"]

    inp.accept(num)
    while not (dec(num) == dec(0)):
        move(num, save)
        if dec(num) > dec(0) and dec(num) < dec(4000):
            initialize(roman)
            move(0, ocx)
            rx = 1
            while not (dec(num) == dec(0)):
                div = ws.f("WS-TBL-DIVISOR", rx)
                while not (dec(num) < dec(div)):
                    cx = 1
                    while ws.f("WS-TBL-ROMAN-CH", rx, cx).raw != b" ":
                        compute(ocx, dec(ocx) + dec(1))
                        move(ws.f("WS-TBL-ROMAN-CH", rx, cx),
                             ws.f("WS-ROMAN-CH", int(ocx)))
                        cx += 1
                    compute(num, dec(num) - dec(div))
                rx += 1
            out += display_line("inp=", save, " roman=", roman)
        else:
            out += display_line("inp=", save, " invalid")
        inp.accept(num)

    return bytes(out), {}
```

## Test result
The previous translation was run on a test input that is not one of the
examples above.
stdin = b''
input_files = {}
The translation raised TypeError: '>' not supported between instances of 'CobDecimal' and 'CobDecimal'

Fix the translation. Reply with the complete corrected Python module in one
```python code block. Do not write anything after the code block.

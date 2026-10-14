# Runtime: supported COBOL subset

`cobol_equiv.runtime` implements COBOL data and arithmetic semantics in pure
Python, modelled on GnuCOBOL 3.1.2 with `cobc -std=default`. The behaviour
below is checked by generated oracle cases (`src/cobol_equiv/oracle/rules.py`)
that are compiled and run with GnuCOBOL and compared byte for byte with the
runtime. Results: `results/gnucobol-<version>/oracle_cases.csv`, summary in `results/SUMMARY.md`.
Each section names the oracle rules that cover it.

Coverage limits, stated plainly:

* figurative constants, group moves, `INITIALIZE` and `OCCURS` subscripting
  are covered by a small rule (`figurative_group`, a few dozen cases), not
  by a systematic generator;
* sequential files are covered by `tests/oracle/test_files.py` (four
  inputs), not by the oracle rules;
* the runtime accepts some editing PICTUREs that cobc rejects (for example
  `$$$,$$$.$$CR`); PICTURE validation is not a goal.

When a case is outside the subset the runtime raises
`cobol_equiv.runtime.errors.Unsupported` (or `MoveError` / `PicError`) instead
of guessing. Unsupported cases are counted separately in the results.

## Data description

```python
from cobol_equiv.runtime import Storage, Group, Num, Alnum, Edited, COMP3

ws = Storage("WS", [
    Num("AMOUNT", "S9(5)V99", usage=COMP3, value="0"),
    Group("IN-DATE", [Num("YYYY", "9(4)"), Num("MM", "99"), Num("DD", "99")]),
    Num("IN-DATE-N", "9(8)", redefines="IN-DATE"),
    Group("ENTRY", [Alnum("CODE", "X(3)"), Num("QTY", "9(3)")], occurs=10),
])
ws["AMOUNT"]        # FieldRef
ws.f("QTY", 3)      # QTY(3), subscripts 1-based, outermost first
```

All items share one `bytearray`, so `REDEFINES`, group moves and record I/O
work on the actual bytes. Initial state without `VALUE`: alphanumeric items
spaces, numeric items zero in their USAGE, numeric-edited items the edited
form of zero (GnuCOBOL's default; checked by rule `default_init`). A `VALUE`
clause works like MOVE, except on numeric-edited items, where a figurative
constant fills the item (`VALUE ZERO` gives `000000`, not an edited zero) and
an alphanumeric literal is stored as written (rule `value_clause`).

| Feature | Supported |
|---|---|
| PICTURE symbols | `9 S V X A Z * $ , . + - CR DB B 0 /`, repeat counts `9(5)` |
| USAGE | `DISPLAY`, `COMP-3`, `COMP` (= `BINARY`), `COMP-5` |
| Sign | trailing embedded (overpunch), GnuCOBOL ASCII convention |
| Structure | groups, `OCCURS n` (fixed), `REDEFINES`, `FILLER` |
| Not supported | `P`, `SIGN SEPARATE`, `SIGN LEADING`, `OCCURS DEPENDING ON`, `JUSTIFIED`, `BLANK WHEN ZERO`, `COMP-1/COMP-2`, national data, EBCDIC data |

## Storage formats (rule `encode_literal`, `storage_length`)

* DISPLAY signed: last digit carries the sign. Positive keeps `'0'..'9'`,
  negative is `0x70..0x79` (`'p'..'y'`). This is GnuCOBOL's ASCII
  convention; IBM's EBCDIC convention (`'}'`, `'J'..'R'`) is different and not
  implemented.
* COMP-3: two digits per byte, sign nibble `C` (+), `D` (-), `F` (unsigned).
* COMP: big-endian two's complement. COMP-5: native byte order
  (little-endian on the x86-64 CI runners).
* Binary sizes (GnuCOBOL `binary-size: 1-2-4-8`): 1-2 digits 1 byte, 3-4
  digits 2 bytes, 5-9 digits 4 bytes, 10-18 digits 8 bytes.

## MOVE (rules `move_*`, `edit`)

* Numeric to numeric: decimal point alignment; extra decimal places are
  truncated, never rounded; extra integer digits are truncated on the left.
  Unsigned receivers get the absolute value.
* Sign of a zero result: a USAGE DISPLAY receiver keeps the sender's sign, so
  moving `-10000` to `PIC S9(4)` stores a negative zero (`000p`). A COMP-3
  receiver does the same only from a DISPLAY sender. All other cases give a
  positive zero.
* COMP is truncated to its PICTURE digits (GnuCOBOL `binary-truncate: yes`).
  COMP-5 is not: moving an item holding 99999 to `S9(4) COMP-5` wraps the
  16-bit value to `-31073`.
* A numeric literal that truncates to zero keeps its sign: `MOVE -0.004` to
  `S9V99` stores a negative zero (rule `literal_truncation`).
* Integer numeric to alphanumeric: the PICTURE digits without sign, then
  alphanumeric padding/truncation. Non-integer numeric to alphanumeric is
  rejected by cobc and by the runtime.
* Alphanumeric item to numeric or numeric-edited (rule
  `move_alnum_text_to_num`): the text is converted as GnuCOBOL does
  (libcob `cob_move_alphanum_to_display`): leading spaces are skipped, an
  optional `+` or `-` is read, the digits before the decimal point are
  right-aligned to the receiver's integer places (excess leading digits are
  dropped), digits after it fill the decimal places (excess dropped);
  spaces and commas are skipped; a second decimal point or any other
  character (before the receiver is full) makes the result zero. A USAGE
  DISPLAY receiver keeps a `-` sign even on a zero result. Other receivers
  get the value through a signed temporary of 38 integer and 38 decimal
  digits, then a numeric MOVE.
* Alphanumeric literal to numeric: only when the literal is all digits; it
  is treated as an unsigned integer. Other literals raise `MoveError`.
* Alphanumeric / group moves: left-justified, space-padded, truncated on the
  right. Group moves copy bytes without conversion.
* Refused: an alphanumeric literal to numeric-edited, and numeric-edited
  to numeric or numeric-edited. GnuCOBOL converts these numerically
  (`MOVE "123"` to `ZZZ9` gives `" 123"`); the runtime does not model that
  conversion for literals.
* Figuratives: `SPACES`, `ZEROS`, `HIGH_VALUES`, `LOW_VALUES`, `All("x")`.
* A numeric literal with more integer digits than the receiver is refused
  (cobc warns, and the resulting sign is inconsistent between items).
* Values of 2**63 or more stored into a binary item without ON SIZE ERROR
  are refused: GnuCOBOL 3.1.2 converts them through a 64-bit integer and the
  result is not a decimal truncation.

## Numeric editing (rule `edit`)

`Z`, `*`, `9`, fixed and floating `$`, `+`, `-`, `CR`, `DB`, `.`, `,`, `B`,
`0`, `/`. Details in the docstring of `runtime/edit.py`. Two GnuCOBOL 3.1.2
behaviours worth knowing:

* the first symbol of a floating string consumes one high-order digit; if it
  is non-zero, suppression ends: `1000` edited with `---9` gives `" 000"`;
* a trailing `+` or `-` reads the sender's next digit after the receiver's
  last decimal place; if it is non-zero the value counts as non-zero:
  `-0.5` edited with `ZZZ9-` gives `"   0-"` (rule `edit_trailing_sign`);
* a fixed leading sign or currency symbol combined with a floating string
  (e.g. `-$$$9.99`) is not supported: GnuCOBOL 3.1.2 prints `-` for positive
  values there, as does 3.2 (pinned by `tests/oracle/test_findings.py`).

## Arithmetic (rules `arith_*`, `compute_intermediate`)

```python
from cobol_equiv.runtime import add, compute, dec
err = add([ws["A"], ws["B"]], ws["T"], rounded=True, on_size_error=True)
err = compute(ws["T"], dec(ws["BAL"]) * dec(ws["RATE"]) / 1200, rounded=True)
```

* `ROUNDED` means nearest, ties away from zero (`1.25 -> 1.3`,
  `-1.25 -> -1.3`). Without it, extra decimal places are truncated.
* Size error: the result has more integer digits than the receiver (COMP-5:
  the magnitude exceeds the largest positive value of the binary field, so
  `-32768` is a size error for `S9(4) COMP-5`). With `on_size_error=True`
  the receiver is unchanged and the function returns `True`. Without it the
  value is truncated on the left (COMP-5: wraps).
* Division by zero is a size error; the receiver is unchanged even without
  ON SIZE ERROR.
* A numeric-edited receiver of an arithmetic statement (GIVING or
  COMPUTE) gets the result truncated to the edited item's digit positions
  first, then edited (rule `arith_edited_giving`). A MOVE to an edited item
  edits the sender's digits instead.
* `ADD x TO y` / `SUBTRACT x FROM y` with a single operand and no ON SIZE
  ERROR can be compiled by cobc to an integer fast path with different
  overflow results (rule `arith_single_operand`): an unsigned COMP-5
  receiver wraps (`SUBTRACT 1 FROM` a zero `9(4) COMP-5` gives 65535), and a
  COMP-3 receiver with an even digit count carries into its spare nibble
  (`ADD 1` to `9(4) COMP-3` holding 9999 stores `x'10000F'`). The runtime
  refuses these two outcomes for every single-operand ADD/SUBTRACT, including
  forms where GnuCOBOL takes its general path and the runtime's result would
  have been right (for example an `S9(12)` operand); this over-refusal is
  deliberate because the runtime cannot see which path cobc chose.
* `DIVIDE ... REMAINDER`: remainder = dividend - divisor * q, with q the
  quotient truncated to the quotient item's decimal places. GnuCOBOL stores
  the remainder even when the quotient had a size error.

### Intermediate precision

Intermediate values are exact for `+`, `-` and `*`. Division follows
GnuCOBOL's `cob_decimal_div`: the dividend is scaled by `10**(38 + k)`
(where `k` compensates a negative scale difference), and the integer quotient
is truncated toward zero. So a quotient carries at least 38 decimal places and
is never rounded before the final store. Consequence, checked by rule
`compute_intermediate` and a unit test:

```
COMPUTE X = 1 / 3 * 3           X PIC 9V99  ->  0.99
COMPUTE X ROUNDED = 1 / 3 * 3                ->  1.00
```

Operator order is the order written: `A / B * C` is `(A / B) * C`. The
runtime's `CobDecimal` overloads `+ - * /` with Python precedence, which is
the same as COBOL's for these operators. Exponentiation (`**`) is not
implemented.

### Comparison (`tests/oracle/test_compare.py`)

Since runtime 1.1.0, `CobDecimal` compares by algebraic value, as a COBOL
numeric relation condition does: `==`, `!=`, `<`, `<=`, `>`, `>=` against
another `CobDecimal`, an `int` or a finite `Decimal`. The scale does not
matter (`dec("1.50") == dec("1.5")`) and a negative zero equals zero.
`hash` is that of the same value as an `int` or `Decimal`, so equal values
are one set element or dict key. Other operands (a `FieldRef`, a string,
a float) are not compared: `==` gives `False` and `<` raises `TypeError`;
wrap them with `dec()`. A NaN intermediate (division by zero) raises
`ArithmeticError` when compared or hashed. Checked with one program of 1128
pairs of DISPLAY, COMP-3 and COMP items (negative zero included), each
compared with the six relations directly and as arithmetic expressions, on
each compiler version; not a generated rule.

## Versions

`cobol_equiv.runtime.__version__`:

- **1.0.0**: the runtime of commit 50456a3, frozen for the benchmark
  (`docs/benchmark-protocol.md`). `CobDecimal` has no comparison methods:
  `==` and `!=` compare object identity, `<`, `<=`, `>`, `>=` raise
  `TypeError`, and the hash is the identity hash. The version number was
  assigned afterwards (deviation D14).
- **1.1.0**: value comparison and hash of `CobDecimal` (above). Nothing else
  changed.

## STRING, UNSTRING, INSPECT (rules `string_stmt`, `unstring_stmt`, `inspect_stmt`)

`runtime/text.py`: `string`, `unstring` (with `Into` for DELIMITER IN /
COUNT IN), `inspect_tallying`, `inspect_replacing`, `inspect_converting`.
Covered forms: DELIMITED BY SIZE / literal, WITH POINTER, ON OVERFLOW;
UNSTRING with `[ALL] d1 OR [ALL] d2`, no DELIMITED BY, TALLYING IN;
INSPECT ALL / LEADING / FIRST / CHARACTERS with BEFORE / AFTER INITIAL,
several phrases in one statement, CONVERTING. Three details:

* UNSTRING without DELIMITED BY advances the pointer by the characters
  actually taken, not by the receiver size;
* UNSTRING into a numeric or numeric-edited receiver moves each piece as
  alphanumeric text, with the conversion described under MOVE (rule
  `unstring_stmt`);
* INSPECT with several phrases follows GnuCOBOL 3.1.2: each phrase scans
  the whole field in turn and marks what it matched, and later phrases skip
  marked characters. `INSPECT "ABCABC" TALLYING C1 FOR ALL "BC" C2 FOR ALL
  "AB"` gives C1=2, C2=0. GnuCOBOL tickets #991 and #992 discuss whether
  this matches the ISO rules (see `docs/findings.md`); we have not read the
  standard text and make no claim about it.

## Reference modification (`tests/oracle/test_refmod.py`)

`refmod(item, start, length=None)` returns an alphanumeric view of bytes
`start .. start + length - 1` (1-based) of the item, sharing its storage,
so it can be a sender or a receiver. Without a length it runs to the end of
the item. A start or length that leaves the item raises `Unsupported`
(GnuCOBOL without runtime checks would read or write outside it). Checked
with one program of 61 MOVEs between reference-modified alphanumeric and
numeric DISPLAY items on each compiler version, not by a generated rule.

## Sequential files

`runtime/files.py` reads and writes LINE SEQUENTIAL and fixed-length record
sequential files as byte strings. Observed GnuCOBOL 3.1.2 behaviour for LINE
SEQUENTIAL: short lines are padded with spaces, long lines truncated, carriage
returns dropped (also inside a line); WRITE removes trailing spaces. Checked by
`tests/oracle/test_files.py`.

## ACCEPT from standard input (`tests/oracle/test_accept.py`)

```python
from cobol_equiv.runtime import Stdin
inp = Stdin(stdin_bytes)
inp.accept(ws["N"])
```

One line per ACCEPT, without its newline; after the last line GnuCOBOL
supplies a single space. The line is moved to the receiver as alphanumeric
data (the conversion above for numeric receivers); for a numeric USAGE
DISPLAY receiver it is first cut to the receiver's length in bytes. Checked
with one program and 36 input lines on each compiler version, not by a
generated rule.

## DISPLAY (rule `display_format`)

`display_line(*items)` returns the bytes the DISPLAY statement writes:
alphanumeric and edited items as stored; numeric items with a leading sign if
the PICTURE has `S`, all digit positions, and `.` before the decimal places.
A negative zero is shown with `+`. COMP-5 items show 3/5/10/20 digits for
1/2/4/8 bytes and no decimal point.

## What "validated" means here

A rule is validated for the PICTUREs, USAGEs and values that the generator
produces (boundaries: zero, one unit in the last place, maximum, negative
maximum, ties ending in 5, plus seeded random values). It is evidence, not a
proof. The runtime models GnuCOBOL 3.1.2; the same oracle cases are also
run with GnuCOBOL 3.2, and `results/SUMMARY.md` shows per rule where 3.2
gives other results (`docs/findings.md` explains each group).

# Runtime: supported COBOL subset

`cobol_equiv.runtime` implements COBOL data and arithmetic semantics in pure
Python, modelled on GnuCOBOL 3.1.2 with `cobc -std=default`. Every rule below
is exercised by generated oracle cases (`src/cobol_equiv/oracle/rules.py`)
that are compiled and run with GnuCOBOL and compared byte for byte with the
runtime. Results: `results/oracle_cases.csv`, summary in `results/SUMMARY.md`.

When a case is outside this subset the runtime raises
`cobol_equiv.runtime.errors.Unsupported` (or `MoveError` / `PicError`) instead
of guessing.

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
form of zero (GnuCOBOL's default; checked by rule `default_init`).

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
  COMP-5 is not: `MOVE 99999` to `S9(4) COMP-5` wraps the 16-bit value to
  `-31073`.
* Integer numeric to alphanumeric: the PICTURE digits without sign, then
  alphanumeric padding/truncation. Non-integer numeric to alphanumeric is
  rejected by cobc and by the runtime.
* Alphanumeric to numeric: only when the sender is all digits; it is treated
  as an unsigned integer. Other content (spaces, letters) gives
  implementation-specific results in GnuCOBOL and raises `MoveError` here.
* Alphanumeric / group moves: left-justified, space-padded, truncated on the
  right. Group moves copy bytes without conversion.
* Figuratives: `SPACES`, `ZEROS`, `HIGH_VALUES`, `LOW_VALUES`, `All("x")`.
* A numeric literal with more integer digits than the receiver is refused
  (cobc warns, and the resulting sign is inconsistent between items).
* Values of 2**63 or more stored into a binary item without ON SIZE ERROR
  are refused: GnuCOBOL 3.1.2 converts them through a 64-bit integer and the
  result is not a decimal truncation.

## Numeric editing (rule `edit`)

`Z`, `*`, `9`, fixed and floating `$`, `+`, `-`, `CR`, `DB`, `.`, `,`, `B`,
`0`, `/`. Details in the docstring of `runtime/edit.py`. Two behaviours that
differ from a naive reading of the standard:

* the first symbol of a floating string consumes one high-order digit; if it
  is non-zero, suppression ends: `1000` edited with `---9` gives `" 000"`;
* a fixed leading sign or currency symbol combined with a floating string
  (e.g. `-$$$9.99`) is not supported: GnuCOBOL 3.1.2 prints `-` for positive
  values there (pinned by `tests/oracle/test_gnucobol_quirks.py`).

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

## STRING, UNSTRING, INSPECT (rules `string_stmt`, `unstring_stmt`, `inspect_stmt`)

`runtime/text.py`: `string`, `unstring` (with `Into` for DELIMITER IN /
COUNT IN), `inspect_tallying`, `inspect_replacing`, `inspect_converting`.
Covered forms: DELIMITED BY SIZE / literal, WITH POINTER, ON OVERFLOW;
UNSTRING with `[ALL] d1 OR [ALL] d2`, no DELIMITED BY, TALLYING IN;
INSPECT ALL / LEADING / FIRST / CHARACTERS with BEFORE / AFTER INITIAL,
several phrases in one statement, CONVERTING. One detail: UNSTRING without
DELIMITED BY advances the pointer by the characters actually taken, not by
the receiver size.

## Sequential files

`runtime/files.py` reads and writes LINE SEQUENTIAL and fixed-length record
sequential files as byte strings. Observed GnuCOBOL 3.1.2 behaviour for LINE
SEQUENTIAL: short lines are padded with spaces, long lines truncated, a CR
before LF dropped; WRITE removes trailing spaces. This module is checked only
through the corpus programs that use files, not by oracle rules.

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
proof, and it is evidence about GnuCOBOL 3.1.2 only.

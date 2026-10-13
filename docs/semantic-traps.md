# Semantic traps

COBOL behaviours that a translation is likely to get wrong, observed with
GnuCOBOL 3.1.2 (`cobc -std=default`). Each one names the test or oracle rule
in this repository that shows it. Other compilers can differ; see "Known
limits" in the README.

### 1. Division inside COMPUTE truncates, it does not round

`COMPUTE X = 1 / 3 * 3` with `X PIC 9V99` gives `0.99`. The quotient keeps
at least 38 decimal places and is truncated, then multiplied, then truncated
to the receiver. With ROUNDED the result is `1.00`. Evaluating the whole
expression exactly (Python `Fraction`) or in floating point gives `1.00` in
both cases.
Backed by: `tests/test_runtime_unit.py::test_division_intermediate_truncates`,
oracle rule `compute_intermediate`.

### 2. ROUNDED is half away from zero

`1.25 -> 1.3`, `-1.25 -> -1.3`. Python's `round()` and `Decimal`'s default
context round half to even (`1.25 -> 1.2`).
Backed by: `test_rounding_ties_away_from_zero`; oracle rules `arith_*`.

### 3. Without ROUNDED, extra decimals are cut, never rounded

Both in MOVE and in arithmetic. `MOVE 1.239 TO X` with `X PIC 9V99` gives
`1.23`.
Backed by: oracle rules `move_num_to_num`, `literal_truncation`; mutants
`interest-truncated` (loancalc), `multiply-not-rounded` (sizeerr).

### 4. Overflow: ON SIZE ERROR keeps the old value, otherwise digits are lost on the left

`ADD 999 TO X` with `X PIC S9(3)` holding 5: with ON SIZE ERROR, X stays 5;
without it, X becomes 4 (1004 with the thousands digit dropped). No error is
raised in either case.
Backed by: `test_size_error_leaves_target_unchanged`; mutants
`size-error-stores` (sizeerr), `amount-no-truncation` (tables).

### 5. Division by zero leaves the receiver unchanged

Even without ON SIZE ERROR.
Backed by: oracle rules `arith_divide_*` (cases with a zero divisor), corpus
program `sizeerr` (vector 2).

### 6. Negative zero exists

Moving `-10000` to `PIC S9(4)` stores `000p`: zero digits with a negative
sign. MOVE of a DISPLAY item, or of a literal, keeps the sign even when every
kept digit is zero; DISPLAY then prints `+0000`.
Backed by: `test_negative_zero_after_truncation`,
`test_literal_truncated_to_zero_keeps_sign`; oracle rules `move_num_to_num`
("zero sign" cases), `display_format`.

### 7. Signs live inside digits

Signed DISPLAY numbers carry the sign in the last character (`-12.34` in
`S9(3)V99` is `0123t`; GnuCOBOL's ASCII convention, not IBM's EBCDIC one).
COMP-3 uses a sign nibble: `C`, `D`, and `F` for unsigned items. Reading such
fields as plain text or declaring them unsigned changes values.
Backed by: `test_overpunch_and_packed_encodings`; mutants `qty-unsigned`
(redef), `packed-gross-unsigned` (payroll).

### 8. COMP and COMP-5 truncate differently

`COMP` is cut to its PICTURE digits (99999 into `S9(4) COMP` gives 9999 by
MOVE). `COMP-5` keeps the binary value and wraps (99999 into `S9(4) COMP-5`
gives -31073). Under ON SIZE ERROR, `S9(4) COMP-5` rejects -32768 although it
fits in 16 bits.
Backed by: `test_comp5_wraps_and_comp_truncates`; oracle rule `binary_store`;
mutant `binary-no-truncation` (sizeerr).

### 9. The same statement can take different code paths

`SUBTRACT 1 FROM U` with `U PIC 9(4) COMP-5` holding 0 gives 65535, while the
general arithmetic path stores the absolute value 1. `ADD 1` to a
`9(4) COMP-3` item holding 9999 stores `x'10000F'`. The runtime refuses these
cases.
Backed by: `tests/oracle/test_gnucobol_quirks.py::test_single_operand_subtract_wraps_unsigned_comp5`;
oracle rule `arith_single_operand`.

### 10. Numeric editing is more than formatting

- `ZZZ.ZZ` with zero gives all spaces; `***.**` gives `***.**`.
- The first symbol of a floating string consumes a digit: 1000 in `---9`
  gives `" 000"`.
- A trailing sign looks at the next truncated digit: -0.5 in `ZZZ9-` gives
  `"   0-"`.
- `-$$$9.99` prints `-` for positive values in GnuCOBOL 3.1.2 (the runtime
  refuses this picture).
- A Python format string is not a substitute: after high-order truncation
  COBOL zero-suppresses what is left (1000123.45 in `ZZZ,ZZ9.99-` gives
  `"    123.45 "`, a format string sliced to 11 characters gives
  `"000,123.45 "`); mutant `format-instead-of-edit` in report.

Backed by: `test_edit`, `test_trailing_sign_reads_next_sender_digit`,
`test_fixed_minus_with_floating_currency_prints_minus_for_positive`; oracle
rules `edit`, `edit_trailing_sign`; corpus program `report`.

### 11. DIVIDE ... REMAINDER uses the truncated quotient

The remainder is `dividend - divisor * q`, with q truncated to the quotient
item's decimals, even when the quotient is ROUNDED. GnuCOBOL stores the
remainder even when the quotient had a size error.
Backed by: `test_divide_remainder`,
`test_remainder_stored_despite_quotient_size_error`; mutant
`remainder-from-rounded-quotient` (sizeerr).

### 12. LINE SEQUENTIAL files are not just lines

READ pads short lines with spaces and drops the rest of long lines; WRITE
removes trailing spaces.
Backed by: `tests/oracle/test_files.py`; mutant `trailing-spaces-kept`
(ctlbreak).

### 13. INSPECT with several phrases

GnuCOBOL handles the phrases one after another, not character by character:
`INSPECT "ABCABC" TALLYING C1 FOR ALL "BC" C2 FOR ALL "AB"` gives C1=2, C2=0.
Backed by: `test_inspect_phrases_processed_one_after_another`; oracle rule
`inspect_stmt`.

### 14. Spaces in numeric fields

`MOVE` of alphanumeric data containing spaces or letters to a numeric item
gives results that depend on the form of the statement in GnuCOBOL: in a
manual probe, `MOVE "ABC"` (a literal) to a `9(3)` item stored `"A C"`,
while moving an item holding `"ABC"` stored `"000"`. These probes are not
part of the test suite. The runtime raises an error for such data; a
translation should treat it as invalid input, not as zero.
Backed by: `test_alnum_moves_and_figuratives` (the runtime refusal only).

### 15. Floating-point errors hide well

A float-based translation is right on most inputs and wrong on some: values
near or at a half-cent tie (binary approximation on the wrong side of it, or
Python's `round()` rounding exact ties to even), and values long enough to
lose digits. Of the nine float mutants in the committed run, three were
killed, two are argued equivalent, and four survived the regression vectors
and up to 200 generated inputs without being equivalent (`float-payment` in
loancalc, `float-gross` in payroll, `float-divide` in sizeerr,
`float-discount` in redef). `float-gross` and `float-discount` were killed in
runs with the earlier input generator, which shows how much detection
depends on the sample. Random testing alone is weak against this class of
error; vectors with deliberate ties are needed.
Backed by: `results/mutation.csv`.

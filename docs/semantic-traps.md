# Semantic traps

COBOL behaviours that a translation is likely to get wrong. Each entry says
which GnuCOBOL versions it was observed on (3.1.2 and 3.2, `cobc
-std=default`) and names the test or oracle rule in this repository that
shows it. Unless an entry says otherwise, both versions behave the same.
How each GnuCOBOL-specific behaviour was checked (tickets, NEWS) is in
[findings.md](findings.md). Other compilers can differ; see "Known limits" in
the README.

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

GnuCOBOL 3.1.2 and 3.2 behaviour: moving `-10000` to `PIC S9(4)` stores
`000p`: zero digits with a negative sign. MOVE of a DISPLAY item, or of a
literal, keeps the sign even when every kept digit is zero; DISPLAY then
prints `+0000`. One case differs between the versions: a MOVE between
COMP-3 items that drops low-order digits of a negative value (`-0.004` from
`S9V999 COMP-3` to `S9V99 COMP-3`) gives `x'000C'` on 3.1.2 and `x'000D'` on
3.2; high-order truncation (`-10000` to `S9(4) COMP-3`) gives `x'00000D'` on
both (`results/version_diff.csv`).
Backed by: `findings/neg_zero.cob`, `test_negative_zero_after_truncation`,
`test_literal_truncated_to_zero_keeps_sign`; oracle rules `move_num_to_num`
("zero sign" cases), `display_format`.

### 7. Signs live inside digits

Signed DISPLAY numbers carry the sign in the last character (`-12.34` in
`S9(3)V99` is `0123t`; GnuCOBOL's ASCII convention, not IBM's EBCDIC one).
COMP-3 uses a sign nibble: `C`, `D`, and `F` for unsigned items. Reading such
fields as plain text or declaring them unsigned changes values. On 3.2 only,
MOVE of an unsigned COMP-3 item to a signed one keeps `F` (GnuCOBOL ticket
#904), and the receiver then fails `IS NUMERIC`.
Backed by: `test_overpunch_and_packed_encodings`; mutants `qty-unsigned`
(redef), `packed-gross-unsigned` (payroll).

### 8. COMP and COMP-5 truncate differently

GnuCOBOL 3.1.2 and 3.2 behaviour: `COMP` is cut to its PICTURE digits
(99999 into `S9(4) COMP` gives 9999 by MOVE). `COMP-5` keeps the binary value
and wraps (99999 into `S9(4) COMP-5` gives -31073). Under ON SIZE ERROR,
`S9(4) COMP-5` rejects -32768 although it fits in 16 bits.
Backed by: `findings/comp5.cob`, `test_comp5_wraps_and_comp_truncates`;
oracle rule `binary_store`; mutant `binary-no-truncation` (sizeerr).

### 9. The same statement can take different code paths

GnuCOBOL 3.1.2 and 3.2 behaviour: `SUBTRACT 1 FROM U` with
`U PIC 9(4) COMP-5` holding 0 gives 65535, while the general arithmetic path
stores the absolute value 1. `ADD 1` to a `9(4) COMP-3` item holding 9999
stores `x'10000F'`. The runtime refuses these cases.
On 3.2 only, `ADD x TO y ROUNDED` with a COMP-3 receiver does not round
(GnuCOBOL ticket #934): 1.00 + 0.005 gives 1.00, not 1.01.
Backed by: `findings/fastpath.cob`, `findings/rounded_comp3.cob`; oracle
rules `arith_single_operand`, `arith_rounded_single_operand`.

### 10. Numeric editing is more than formatting

- `ZZZ.ZZ` with zero gives all spaces; `***.**` gives `***.**`.
- The first symbol of a floating string consumes a digit: 1000 in `---9`
  gives `" 000"`.
- A trailing sign looks at the next truncated digit: -0.5 in `ZZZ9-` gives
  `"   0-"`.
- `-$$$9.99` prints `-` for positive values in GnuCOBOL 3.1.2 and 3.2 (the
  runtime refuses this picture).
- A Python format string is not a substitute: after high-order truncation
  COBOL zero-suppresses what is left (1000123.45 in `ZZZ,ZZ9.99-` gives
  `"    123.45 "`, a format string sliced to 11 characters gives
  `"000,123.45 "`); mutant `format-instead-of-edit` in report.

Backed by: `test_edit`, `test_trailing_sign_reads_next_sender_digit`,
`findings/edit_minus.cob`; oracle rules `edit`, `edit_trailing_sign`; corpus
program `report`.

### 11. DIVIDE ... REMAINDER uses the truncated quotient

The remainder is `dividend - divisor * q`, with q truncated to the quotient
item's decimals, even when the quotient is ROUNDED. GnuCOBOL 3.1.2 and 3.2
store the remainder even when the quotient had a size error.
Backed by: `test_divide_remainder`, `findings/remainder.cob`; mutant
`remainder-from-rounded-quotient` (sizeerr).

### 12. LINE SEQUENTIAL files are not just lines

READ pads short lines with spaces; WRITE removes trailing spaces. A line
longer than the record is truncated by GnuCOBOL 3.1.2 but returned as
further records by 3.2. 3.2 ends the test program on a carriage return
inside a record (the only control character tested; its NEWS says such a
READ "may" return status 09). The corpus program `strproc` fails on 3.2
for the first reason.
Backed by: `tests/oracle/test_files.py`; mutant `trailing-spaces-kept`
(ctlbreak); `results/gnucobol-3.2/corpus.csv`.

### 13. INSPECT with several phrases

GnuCOBOL 3.1.2 and 3.2 handle the phrases one after another: `INSPECT
"ABCABC" TALLYING C1 FOR ALL "BC" C2 FOR ALL "AB"` gives C1=2, C2=0.
GnuCOBOL tickets #991/#992 discuss this order against the ISO rules (see
findings.md). On 3.2 only, `LEADING "0"` followed by `CHARACTERS` counts one
character more than 3.1.2, and two INSPECT statements with `LEADING "A"` and
`ALL "AA"` can abort the program with a memory error.
Backed by: `test_inspect_phrases_processed_one_after_another`,
`findings/inspect.cob`, `findings/inspect_twice.cob`; oracle rules
`inspect_stmt`, `inspect_iso_example`.

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
Backed by: `results/gnucobol-3.1.2/mutation.csv`.

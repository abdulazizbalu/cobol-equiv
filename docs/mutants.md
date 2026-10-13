# Mutation testing: method and the equivalent mutants

Each corpus program has a `mutants.py` with deliberately wrong copies of its
reference translation (`harness/mutation_run.py`). Counts and the reason
each surviving mutant survives are in `results/SUMMARY.md` and
`results/gnucobol-3.1.2/mutation.csv`; this file does not repeat them.
Mutation testing runs on GnuCOBOL 3.1.2 only, the version the reference
translations were written against.

## Two measurements

- **(a)** the fixed regression vectors of the program spec, then the
  Hypothesis-generated inputs (seeded from the program name, so every
  mutant of a program sees the same inputs).
- **(b)** the same, plus the boundary vectors of `harness/boundary.py`. They
  are built from the PICTURE and USAGE of each input record item only: zero,
  one unit of the last decimal place, the maximum and one less, the smallest
  value with all digits, the truncation boundaries 10^k - 1 and 10^k, the
  rounding ties 5 x 10^k units of the last place (0.05, 0.50, 5.00, ... for
  two decimals), the negatives of all of these and a negative zero for
  signed DISPLAY items; spaces, one character and full-length values for
  alphanumeric items. Records vary one item at a time from a base record,
  plus records where every item takes its i-th value; they are cut into
  files of the spec's maximum record count, plus an empty file. The
  generator does not read mutants, reference translations, value overrides
  or program logic, so the set is the same for any translation of the same
  record layouts.

A mutant counts as killed in (b) if (a) killed it or a boundary vector
does. Both columns are reported side by side.

## Equivalent mutants

A mutant labelled `equivalent` survives by construction: it cannot change
the output for any input the program accepts. Each label below is backed
either by running the reference and the mutated code on every value of a
bounded input domain (`tests/test_equivalent_mutants.py`), or by an explicit
argument, or both. The mutation run reports a label as "disproved" if (a) or
(b) kills the mutant, and `tests/test_equivalent_mutants.py` fails if the
committed run has such a row.

### `loancalc/mrate-half-even`

The monthly rate `RATE / 1200` is rounded to 8 decimals half-to-even
instead of ROUNDED (GnuCOBOL default: half away from zero). LN-RATE is `99V999`, so
RATE = k / 1000 with 0 <= k <= 99999, and RATE / 1200 x 10^8 = 250k / 3,
whose fractional part is 0, 1/3 or 2/3, never 1/2. Without a tie the two
rounding modes agree. Exhaustive check: the original and the mutated
statement for all 100000 values of LN-RATE give the same bytes in
WS-MRATE.

### `loancalc/residual-abs`

The residual is printed from `abs(WS-BALANCE)` instead of WS-BALANCE.
Argument: WS-BALANCE starts as LN-PRINCIPAL (unsigned, so >= 0). Each month
subtracts WS-PRINC-PART, which is replaced by WS-BALANCE itself whenever it
exceeds WS-BALANCE, so the subtraction never takes the balance below zero; a
negative WS-PRINC-PART (payment below the interest) only increases it, and
high-order truncation of a non-negative result stays non-negative. So the
balance is never negative, and abs() does not change it. Argument only.

### `loancalc/loop-limit-gt`

The loop ends on `WS-MONTH > TERM` instead of `>= TERM` (it also ends on
`BALANCE <= 0` in both). Argument: in the month where WS-MONTH = TERM the
principal part is set to the whole balance, so the balance is 0 after that
month and the loop ends on `BALANCE <= 0` in both versions, after the same
number of months. If the balance reaches 0 earlier, both stop then. TERM 0
is rejected before the loop. Argument only.

### `payroll/overtime-ge-40`

Overtime is computed from 40 hours inclusive (`>=`). The two conditions
differ only at EMP-HOURS = 40.0, where the overtime branch computes
`40 x RATE + 0 x RATE x 1.5` and the regular branch `40.0 x RATE`, and both
leave WS-OT-HOURS zero. Exhaustive check: the whole IF statement, taken from
the reference and from the mutated source, leaves the same storage bytes for
every EMP-RATE 0.00 .. 999.99 at 40.0 hours. Everything after the IF reads
only storage, so the rest of the program behaves the same.

### `payroll/bracket-lt`

The first tax bracket is `< 1000` instead of `<= 1000`. The two differ only
when WS-GROSS = 1000.00, where the first bracket gives 1000.00 x 0.10 =
100.00 and the second 100 + 0 x 0.25 = 100.00. Check: every combination of
hours below 40 (in tenths) and whole-cent rate that gives a gross of exactly
1000.00, plus 40.0 x 25.00 and the overtime case 80.0 x 10.00, through the
whole IF; same output for reference and mutant.

### `tables/rank-sign`

The rank line moves `-WS-QTY` to `WL-QTY` (`ZZ,ZZ9`). The edited picture
has no sign position, so the sign is dropped. Exhaustive check: every
WS-QTY (`9(5)`) value 0 .. 99999 gives the same bytes in WL-QTY.

### `datecalc/python-floor-division` and `datecalc/year-unsigned-ignored`

The first replaces `DIVIDE WS-Y BY 4` (truncating) with Python floor
division; the second declares WS-Y signed. Both can only matter if WS-Y is
negative. Argument: DATE-TO-NUM sets WS-Y = WS-YYYY - 1601 and is called
(1) after VALIDATE-DATE, which rejects years below 1601, and (2) from
NUM-TO-DATE, where WS-YYYY starts at WS-DAYNUM / 366 + 1601 with WS-DAYNUM
>= 0 (out-of-range day numbers are rejected before) and is only incremented,
or decremented right after an increment. NUM-TO-DATE also sets WS-Y =
WS-DAYNUM / 366 >= 0. So WS-Y is never negative. Exhaustive check: DATE-TO-
NUM for every WS-YYYY 1601 .. 9999 gives the same WS-DAYNUM, WS-Q and WS-Y
value in the reference and both mutants.

### `classify/float-compare`

The balance is converted to a Python float before the comparisons.
CU-BALANCE (`S9(7)V99`) is used only in comparisons with 0, 1000, 10000,
50000 and -500. Argument: every balance is n / 100 with |n| < 10^9; its
float differs from it by less than 2^-53 x 10^7 < 1.2 x 10^-9, while a
balance that differs from a threshold differs by at least 0.01, so the float
lies on the same side of every threshold; a balance equal to a threshold
converts to exactly that integer. Negative zero converts to -0.0, which is
not below 0, as in the reference. Partial check: every balance within 1.00
of each threshold and the two extremes, for business and personal
customers and four lateness classes.

## Re-classified

### `ctlbreak/float-total` (was equivalent, now missed)

The branch total is accumulated in a Python float and moved into
WS-BRANCH-TOT (`S9(7)V99`). The earlier label rested on the float sum being
exact to the cent for short files. That does not cover every input: with
101 records of 99999.99 in one branch the total passes 9,999,999.99;
the reference truncates it, as GnuCOBOL does, while the mutant's MOVE of
the float sum is refused by the runtime, and the harness reports the
difference (`test_ctlbreak_float_total_is_not_equivalent`, run against
GnuCOBOL). Generated and boundary files have at most 30 records, so neither
measurement reaches such a total; the mutant is reported as missed in both.

## Limits

- The exhaustive checks cover the mutated statement over its input domain;
  that the rest of the program cannot tell the two apart is part of the
  argument, not of the check.
- `loancalc/residual-abs`, `loancalc/loop-limit-gt` and the general case of
  `classify/float-compare` rest on arguments only.
- The boundary vectors are general, not a proof of coverage; a mutant that
  survives both measurements may still be detectable with a longer or
  differently shaped input (as `ctlbreak/float-total` shows).

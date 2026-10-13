# GnuCOBOL behaviours found while validating the runtime

Each entry is a behaviour of GnuCOBOL that a Python translation must
reproduce, or that the runtime refuses to model. Each one has a small COBOL
program in `tests/oracle/findings/` whose output on every supported
compiler version is pinned by `tests/oracle/test_findings.py`; CI runs that
test with GnuCOBOL 3.1.2 (Ubuntu 24.04 package `gnucobol3`) and GnuCOBOL
3.2 (built from the release tarball, `scripts/build-gnucobol-3.2.sh`).

How the entries were checked, and the limits of that check:

- **Reproduced** on both compiler versions with the program named in each
  entry, compiled with `cobc -x -std=default`.
- **GnuCOBOL sources consulted:** the NEWS file of the 3.2 release tarball,
  its `config/default.conf`, and the GnuCOBOL bug tracker on SourceForge
  (searched for the terms listed per entry). The tracker
  search is a keyword search, not a review of every ticket; "no ticket
  found" means only that.
- **Not consulted:** the GnuCOBOL Programmer's Guide and anything on
  gnu.org (not reachable from the machine used for this check), and the text of the COBOL standard (ISO/IEC 1989), which we do
  not have. So nothing here claims that GnuCOBOL deviates from the
  standard. Where a ticket quotes the standard or argues from it, the
  entry says so and attributes the statement to the ticket.
- **3.2 tarball provenance:** SHA-256
  `3bb48af46ced4779facf41fdc2ee60e4ccb86eaa99d010b36685315df39c2ee2`,
  computed from the SourceForge download; its SHA-1 and MD5 match the values
  SourceForge publishes for `gnucobol-3.2.tar.xz`. The GPG signature
  (`gnucobol-3.2.tar.xz.sig`, key `B9459D0CA8A740B323235CDF13E96B53C005604E`)
  was not verified because no keyserver was reachable from this environment.

## Behaviours shared by 3.1.2 and 3.2

### Negative zero after high-order truncation

GnuCOBOL 3.1.2 and 3.2 behaviour: `MOVE` of `-10000` (`S9(6)`) to `S9(4)`
stores `000p`, digits zero with a negative sign; `ADD -10000` to a zero
`S9(4)` does the same, and `ADD -100000` to `S9(5) COMP-3` stores
`x'00000D'`. DISPLAY prints such an item as `+0000`, and it compares equal
to zero.
Program: `findings/neg_zero.cob`. The 3.2 NEWS says: "numeric DISPLAY can
store and may contain a positive zero after arithmetic, PACKED-DECIMAL may
contain negative zero (x'0D') after arithmetic; as before numeric
comparisions to ZERO / 0 / +0 / -0 will all be identical". The program above
still gives `000p` for DISPLAY on 3.2. Where the two versions do differ is
MOVE between COMP-3 items (`results/version_diff.csv`, rule
`move_num_to_num`, "zero sign" cases): `-0.004` moved from `S9V999 COMP-3`
to `S9V99 COMP-3` gives `x'000C'` on 3.1.2 and `x'000D'` on 3.2.
Tracker search ("negative zero"): no ticket found.

### COMP-5 is not truncated to its PICTURE; its size-error range is symmetric

GnuCOBOL 3.1.2 and 3.2 behaviour: moving an item holding 99999 to
`S9(4) COMP-5` stores the 16-bit value -31073, while `S9(4) COMP` stores
9999. Under ON SIZE ERROR, adding -32768 to a zero `S9(4) COMP-5` raises
the size error (the item stays 0) although -32768 fits in 16 bits; adding
12345 does not raise it.
Program: `findings/comp5.cob`. `config/default.conf` in the 3.2 tarball sets
`binary-truncate: yes` with the comment "Numeric truncation according to
ANSI"; the observed COMP / COMP-5 difference is consistent with that option
applying to COMP only, but we have not found a GnuCOBOL document that says
so. Tracker search ("COMP-5", "binary-truncate"): no ticket found.

### REMAINDER is stored although the quotient had a size error

GnuCOBOL 3.1.2 and 3.2 behaviour: `DIVIDE A BY B GIVING Q REMAINDER R ON
SIZE ERROR ...` with A = 12345, B = 10 and `Q PIC S9(2)` takes the size-error
branch and leaves Q unchanged, but stores R = 5.
Program: `findings/remainder.cob`. Tracker search ("REMAINDER"): tickets
#786 and #1183 are about the DIVIDE documentation, not this behaviour. We
make no claim about what the standard requires here.

### Single-operand ADD / SUBTRACT can take an integer path

GnuCOBOL 3.1.2 and 3.2 behaviour: `SUBTRACT 1 FROM U` with
`U PIC 9(4) COMP-5` holding 0 stores 65535; `ADD 1 TO P` with
`P PIC 9(4) COMP-3` holding 9999 stores `x'10000F'` (the carry goes into
the unused high-order nibble). The oracle cases with two operands (rules
`arith_add_to`, `arith_subtract_from`, ...) give the absolute value and a
truncation to the PICTURE digits instead, which is what the runtime
models. Which single-operand forms take the integer path depends on the
operand; the runtime cannot see that, so it refuses the two outcomes above
for every single-operand ADD/SUBTRACT without ON SIZE ERROR.
Program: `findings/fastpath.cob`. Tracker search ("ADD 1 overflow",
"cob_add_int", "packed decimal overflow"): no ticket found for these two
outcomes.

### `-$$$9.99` prints a minus sign for positive values

GnuCOBOL 3.1.2 and 3.2 behaviour: with `PIC -$$$9.99`, +5 is edited as
`"-  $5.00"` (the same as -5), and +1000 as `" 1000.00"` (no currency
sign). The runtime refuses pictures that combine a fixed sign or currency
symbol with a floating string.
Program: `findings/edit_minus.cob`. Tracker search ("floating insertion",
"PICTURE edit sign"): no ticket found.

### INSPECT with several phrases handles the phrases one after another

GnuCOBOL 3.1.2 and 3.2 behaviour: `INSPECT X TALLYING C1 FOR ALL "BC" C2
FOR ALL "AB"` with X = "ABCABC" gives C1=2, C2=0, and the matching
REPLACING gives "AxyAxy": the first phrase scans the whole field first and
the second phrase cannot use characters the first one matched.
Program: `findings/inspect.cob`. GnuCOBOL tickets #991 and #992 (opened by
Robert Dubner, 2024-09-22) discuss INSPECT with several phrases: #991 runs
an example that it attributes to appendix D.25 of ISO/IEC 1989:2023 and
states the expected counts 03 01 01 00 05; a comment there describes
INSPECT as checking every phrase at each character position before moving
on (the comment does not quote the standard). In #992 the GnuCOBOL
maintainer writes that "the internal 'already done' is reset within the
statement" and accepts the ticket (status accepted, milestone GC 3.x, last
updated 2025-01-24). By the description in that comment, the program above
would give C1=0, C2=2; we have not read the standard and do not claim what
it requires.

## Behaviours that differ between 3.1.2 and 3.2

`results/version_diff.csv` lists every oracle case whose GnuCOBOL output
differs between the two versions; `results/SUMMARY.md` counts them per rule.
The differences fall into the groups below.

### INSPECT: LEADING followed by CHARACTERS (3.2 counts one more)

`INSPECT Z TALLYING C1 FOR LEADING "0" C2 FOR CHARACTERS` with Z = "0000":
3.1.2 gives C2 = 0, 3.2 gives C2 = 1. In the ticket #991 example
(rule `inspect_iso_example`), 3.1.2 gives the counts the ticket states as
expected (03 01 01 00 05) and 3.2 gives 03 01 01 00 06, which is the result
the ticket reports. Program: `findings/inspect.cob`.

### INSPECT: two statements abort the program on 3.2

Two `INSPECT ... TALLYING C1 FOR LEADING "A" C2 FOR ALL "AA"` statements,
the second on a longer field, end the program on 3.2 with "attempt to
reference invalid memory address" and "free(): corrupted unsorted chunks"
(exit status 134); 3.1.2 runs it normally. Program:
`findings/inspect_twice.cob` (found by bisecting an oracle program that
aborted; `results/gnucobol-3.2/oracle_aborts.csv`). Tracker search
("INSPECT"): ticket #992 mentions "corrupt REPLACING"; no ticket found that
reports this abort. Because a program that aborts may already have produced
wrong results, the oracle reruns every case of an aborted program on its
own (see `oracle/run.py`).

### ADD ... ROUNDED into COMP-3 does not round on 3.2

`ADD A TO T ROUNDED` with A = 0.005 (`S9V999`) and T = 1.00
(`S9(5)V99 COMP-3`) gives 1.01 on 3.1.2 and 1.00 on 3.2; the same statement
with a DISPLAY receiver gives 1.01 on both (rule
`arith_rounded_single_operand`). Program: `findings/rounded_comp3.cob`.
GnuCOBOL ticket #934 ("BCD ADD/SUBTRACT does not apply default ROUNDED
mode", status closed) describes this: the optimised COMP-3 add "was shipped
with GC 3.2" and loses the default ROUNDED mode; the fix is in a later
version (milestone GC 3.x).

### MOVE of unsigned COMP-3 to signed COMP-3 keeps sign nibble F on 3.2

`MOVE` of `9(3) COMP-3` holding 51 to `S9(3) COMP-3` stores `x'051C'` on
3.1.2 and `x'051F'` on 3.2, where the receiver then fails `IS NUMERIC`.
Program: `findings/move_packed_sign.cob`. GnuCOBOL ticket #904 ("MOVE
PACKED-DECIMAL unsigned to signed leads to bad sign", status closed)
describes it and shows the fix to `libcob/numeric.c`, checked in after 3.2
(r5166). The oracle also shows 3.2 carrying digits into the unused
high-order nibble of even-digit COMP-3 receivers on MOVE (rule
`move_num_to_num`).

### Values of 2**63 or more moved to a binary item

Moving -10**30 (`S9(31)`) to `S9(18) COMP` gives -76944270305263616 on 3.1.2
(not a decimal truncation) and 0 on 3.2 (decimal truncation). The runtime
refuses such stores on every version. Program: `findings/huge_comp.cob`.

### LINE SEQUENTIAL files

From the 3.2 NEWS and `tests/oracle/test_files.py`:

- a line longer than the record is truncated by 3.1.2 and returned as
  further records by 3.2 (NEWS: "the default changed (per COBOL 2023 and
  other compilers) so the data is returned as 'multiple' records and a
  warning (status 06) is issued"); `runtime/files.py` supports both with
  `long_lines="truncate"` / `"split"`;
- 3.2 validates record data on READ by default (NEWS: "in case of bad
  printable data (less than SPACE) a READ may result in io status 09");
  a carriage return inside a line ends the test program on 3.2 (it has no
  FILE STATUS clause). The runtime does not model this validation.

The corpus program `strproc` has a regression vector with a line longer
than its record. Its reference translation reads with the 3.1.2 rule, so it
fails on 3.2 (`results/gnucobol-3.2/corpus.csv`).

## What this means for translations

A translation that is byte-exact against one GnuCOBOL version is not
automatically exact against another. Of the behaviours above, the ones
that differ between 3.1.2 and 3.2, three groups are treated as defects
by GnuCOBOL's own tickets: the COMP-3 sign nibble (#904), ROUNDED into
COMP-3 (#934) and INSPECT with several phrases (#991/#992). For the INSPECT
abort, the binary items of 2**63 or more and the LINE SEQUENTIAL changes we
found no ticket, or the NEWS describes the change as intended; a translation targeting
a mainframe compiler should not copy them without checking that
compiler.

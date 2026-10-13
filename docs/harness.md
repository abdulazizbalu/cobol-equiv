# Differential testing harness

`cobol_equiv.harness` runs a COBOL program under GnuCOBOL and a Python
translation on the same inputs and compares their outputs byte for byte.

## Steps

1. **Compile** (`harness/cobol.py`): `cobc -x -std=default`, all inherited
   `COB*` environment variables removed, `LC_ALL=C`. Executables are cached
   in `.cobol-build/` under a hash of the source, the cobc version and the
   flags. Before compiling, the source is rejected if a line is longer than
   72 columns (fixed format would silently drop the rest) or if it reads the
   clock or random numbers (`CURRENT-DATE`, `WHEN-COMPILED`,
   `SECONDS-PAST-MIDNIGHT`, `FUNCTION RANDOM`,
   `ACCEPT ... FROM DATE/DAY/TIME/DAY-OF-WEEK`). This is a text check, not a
   proof of determinism.
2. **Run**: the COBOL executable runs in a fresh temporary directory that
   holds the input files, with the given stdin and a timeout (10 s by
   default). A non-zero exit status is an error of the harness run, not a
   difference. The exit status and stderr are not compared, so RETURN-CODE
   and DISPLAY UPON SYSERR cannot be checked.
3. **Run the translation** in the same process, with a SIGALRM time limit
   (POSIX only). An exception (including `SystemExit`) or a timeout in the
   translation counts as a detected difference.
4. **Compare** stdout and every declared output file. The report gives the
   stream, the line (or record, for fixed-length files), the field name when
   the spec provides a layout for that line, and the expected and actual
   bytes.

## Inputs

Each program has fixed regression vectors and Hypothesis-generated inputs
(`harness/strategies.py`):

- numeric items draw, with equal weight, from boundary values (0, one unit
  in the last place, the maximum, values ending in 5), from values with a
  randomly chosen number of digits, and from Hypothesis' integer strategy
  over the PICTURE range (which favours small values); signed items get
  both signs, signed DISPLAY items sometimes a negative zero;
- alphanumeric items draw printable ASCII (0x20-0x7E);
- a spec can narrow single items (`overrides`), build whole records
  (`record_strategy`, used for REDEFINES variants), or post-process the
  record list (`finalize`, used to sort input for a control break);
- inputs are LINE SEQUENTIAL files with trailing spaces removed, so the
  READ padding is exercised.

Generation is seeded from the program name and uses no example database,
so a run is deterministic for a given Hypothesis version, and every
translation of a program (reference or mutant) sees the same inputs. A
different seed or Hypothesis version gives different inputs, which can change
which mutants a generated input kills. When a generated input fails,
Hypothesis shrinks it and the harness reports the smallest failing input it
found.

## IO contract

```python
def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]
```

`input_files` maps the names the COBOL program ASSIGNs to file contents. The
result is everything written to stdout and the full content of every output
file. A translation must not read the clock, random sources, the network or
the file system.

## Program spec

`corpus/<name>/spec.py` defines `SPEC = ProgramSpec(...)`:

| field | meaning |
|---|---|
| `source` | the COBOL program |
| `inputs` | `InputSpec` per input file or `STDIN`: record layout, record count range, overrides |
| `outputs` | output file names to compare |
| `layouts` | `OutputLayout` per stream: a function from a line to `(field, start, length)` columns, and `record_length` for fixed-length record files |
| `vectors` | regression inputs, `{file name: bytes}`; `make_records()` builds them from field values |

## Commands

```sh
python -m cobol_equiv.harness.check <program dir> <translation.py> [--examples N]
python -m cobol_equiv.harness.corpus_run      # all reference translations -> results/gnucobol-<version>/corpus.csv
python -m cobol_equiv.harness.mutation_run    # all mutants -> results/gnucobol-<version>/mutation.csv
```

## Mutation testing

`corpus/<name>/mutants.py` lists deliberately wrong variants of the reference
translation, each as text edits with a category (`float`, `rounding`,
`truncation`, `sign`, `off-by-one`, `branch`). A mutant is killed when the
harness reports a difference on a vector or a generated input. Each mutant
is measured twice: (a) regression vectors and generated inputs; (b) the same
plus the boundary vectors derived from the PICTURE clauses
(`harness/boundary.py`). Survivors carry a `note` on why the inputs did not
reach the difference; `equivalent: True` marks a mutant that cannot change
the output, justified in [mutants.md](mutants.md).

What the mutation results show, read plainly: most errors in control flow,
signs, truncation and fixed rounding positions are found by the regression
vectors or the generated inputs (vectors run first, so they get the credit
for anything they catch); the survivors and their reasons are listed in
`results/SUMMARY.md`. Floating-point errors are the hardest: they change the
output only on some inputs (half-cent ties, or values long enough to lose
precision), and whether the inputs contain one is partly luck. An independent review found one mutant labelled equivalent that was
not (see `format-instead-of-edit` in `results/gnucobol-3.1.2/mutation.csv`); the labels are
judgements and can be wrong.

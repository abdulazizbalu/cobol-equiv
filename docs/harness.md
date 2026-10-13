# Differential testing harness

`cobol_equiv.harness` runs a COBOL program under GnuCOBOL and a Python
translation on the same inputs and compares their outputs byte for byte.

## Steps

1. **Compile** (`harness/cobol.py`): `cobc -x -std=default`, all inherited
   `COB*` environment variables removed, `LC_ALL=C`. Executables are cached
   in `.cobol-build/` under a hash of the source, the cobc version and the
   flags. Before compiling, the source is rejected if a line is longer than
   72 columns (fixed format would silently drop the rest) or if it reads the
   clock or random numbers (`CURRENT-DATE`, `WHEN-COMPILED`, `RANDOM`,
   `ACCEPT ... FROM DATE/DAY/TIME/DAY-OF-WEEK`).
2. **Run**: the COBOL executable runs in a fresh temporary directory that
   holds the input files, with the given stdin and a timeout (10 s by
   default). A non-zero exit status is an error of the harness run, not a
   difference.
3. **Run the translation** in the same process, with a SIGALRM time limit
   (POSIX only). An exception or a timeout in the translation counts as a
   detected difference.
4. **Compare** stdout and every declared output file. The report gives the
   stream, the line (or record, for fixed-length files), the field name when
   the spec provides a layout for that line, and the expected and actual
   bytes.

## Inputs

Each program has fixed regression vectors and Hypothesis-generated inputs
(`harness/strategies.py`):

- numeric items draw from boundary values (0, one unit in the last place,
  the maximum, values ending in 5) or uniformly from the PICTURE range,
  with both signs for signed items;
- alphanumeric items draw printable ASCII;
- a spec can narrow single items (`overrides`), build whole records
  (`record_strategy`, used for REDEFINES variants), or post-process the
  record list (`finalize`, used to sort input for a control break);
- inputs are LINE SEQUENTIAL files with trailing spaces removed, so the
  READ padding is exercised.

Generation is derandomized and uses no example database, so a run is
deterministic for a given Hypothesis version. When a generated input fails,
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
python -m cobol_equiv.harness.corpus_run      # all reference translations -> results/corpus.csv
python -m cobol_equiv.harness.mutation_run    # all mutants -> results/mutation.csv
```

## Mutation testing

`corpus/<name>/mutants.py` lists deliberately wrong variants of the reference
translation, each as text edits with a category (`float`, `rounding`,
`truncation`, `sign`, `off-by-one`, `branch`). A mutant is killed when the
harness reports a difference on a vector or a generated input. Survivors are
analysed by hand: `equivalent: True` with a `note` when the mutant cannot
change the output on the program's input domain, otherwise a note on why the
inputs did not reach the difference. These notes are judgements; the report
keeps them apart from the counts.

What the mutation results show, read plainly: errors in control flow,
signs, truncation and fixed rounding positions are found quickly, usually by
the regression vectors. Floating-point errors are the hardest: they change
the output only on rare inputs (half-cent ties whose binary value falls on
the wrong side), and random generation rarely produces those.

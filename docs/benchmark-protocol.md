# Benchmark protocol: LLM translations of COBOL to Python

This protocol is fixed before any translation is generated. Changes made
after it was merged are listed, with their reasons, under "Deviations from
protocol" at the end; the text above that section is not edited.

The object being measured is the Python code produced by one large language
model from COBOL source. The measuring instrument is the differential
harness of this repository (`src/cobol_equiv/harness/`), with GnuCOBOL 3.1.2
as the primary oracle.

## 1. Corpus

Two tracks, always reported separately and never pooled.

### Track E: external programs

COBOL programs written by people outside this repository, from public
sources whose license allows use. Candidate sources, screened in this
order:

1. Open Mainframe Project, COBOL Programming Course
   (`github.com/openmainframeproject/cobol-programming-course`, commit
   `1f037d24326124f4f2c5cd2d31e5220ceb549580`), licensed CC BY 4.0. Programs
   are committed with attribution; every change is marked.
2. Rosetta Code COBOL solutions, through the RosettaCodeData mirror
   (`github.com/acmeism/RosettaCodeData`, commit
   `1d475861d7141ef2fafff293d9339f56e4b0f5db`). Rosetta Code content is under
   the GNU Free Documentation License; because redistribution of code under
   that license is not clearly allowed without its conditions, these
   programs are not committed. A script downloads them from pinned URLs and
   checks SHA-256 checksums; adaptations are committed as patches.
3. NIST COBOL85 test suite (`newcob.val`, from the GnuCOBOL file area on
   SourceForge, `newcob.val.tar.gz`, SHA-256
   `e4513f26a9b38911f7bf882fe3d3339a80b45cabc2caf85eb3055b0f5ce87ee0`),
   downloaded by script.

A candidate is kept only if all of the following hold:

- **E1** It compiles with `cobc -x -std=default` (GnuCOBOL 3.1.2) after the
  adaptations allowed below.
- **E2** It is deterministic: no clock, date, random numbers, environment
  variables or command-line arguments.
- **E3** Its output depends on input read with ACCEPT or from a sequential
  file, so that held-out inputs can be generated. A program whose task
  statement names an input that the program hardcodes may be adapted to
  read that value instead (an input/output plumbing change).
- **E4** It is inside the runtime subset documented in `docs/runtime.md`: a
  reference translation using `cobol_equiv.runtime` passes all its fixed,
  generated and boundary vectors on GnuCOBOL 3.1.2. Reference translations
  are never shown to a translator.
- **E5** It has at most 500 source lines.
- **E6** No CALL, embedded SQL or CICS, SORT/MERGE, indexed or relative
  files, SCREEN SECTION, or REPORT SECTION.

Allowed adaptations, each listed per program in its `ADAPTATION.md`:
ASSIGN names and ORGANIZATION LINE SEQUENTIAL for files; removing JCL or
platform-only clauses (e.g. `RECORDING MODE`, `LABEL RECORDS`, `BLOCK
CONTAINS`); replacing a hardcoded task input with ACCEPT (E3); ending the
program with STOP RUN. Nothing else in the logic or data definitions is
changed.

Selection: candidates are screened in the source order above, and within a
source in alphabetical order of file or task name. Every candidate that
meets E1-E6 is kept, up to 30. The target is 20 or more; if fewer qualify,
the real number is reported and nothing is added to reach a target. The
screening record (each candidate, kept or the first criterion it fails) is
committed as `benchmark/corpus-e/screening.csv`.

### Track R: programs written for this repository

The 10 programs in `corpus/` plus about 10 new programs for areas the
corpus lacks: nested PERFORM and GO TO flow, SEARCH ALL, INITIALIZE,
reference modification, COMPUTE with several operators, and multi-level
group items. All Track R programs, specs and reference translations are
committed before the first translation is generated and are not changed
afterwards. In documentation this track is described only as "programs
written for this repository".

### Source shown to the translator

For both tracks, comment lines (indicator `*` or `/` in column 7) and
columns 73-80 are removed before the source is shown. Nothing else is
changed.

## 2. Vectors

Each program has a spec (`spec.py`) with fixed regression vectors, input
generators (Hypothesis) and the PICTURE boundary vectors of
`harness/boundary.py`. The expected output of every vector is what the
program compiled with GnuCOBOL 3.1.2 produces. The vectors are split:

- **VISIBLE**: 2 vectors, shown to the translator with their outputs. They
  are the first two fixed vectors whose inputs are not all empty; if a
  program has fewer than two such vectors, the rest are the first generated
  inputs from the seed `crc32("visible:" + name)`.
- **DEV**: the remaining fixed vectors, then 50 generated inputs from the
  seed `crc32("dev:" + name)`. Used only for repair feedback in condition B.
- **HELD-OUT**: 200 generated inputs from the seed `crc32(name)` (the same
  generation the harness uses now) and all boundary vectors. Never shown to
  any translator. Any held-out input identical to a VISIBLE or DEV input is
  dropped. The final score uses HELD-OUT only.

A translation **passes** a set of vectors when, for every vector in it, its
standard output and every output file are byte-identical to GnuCOBOL's, it
does not raise, does not exceed the time limit, and does not trigger the
runtime's Unsupported error (also when it catches it).

## 3. Translators and conditions

Model: the model configured for the generating session. The recorded name
is the model name the API reports for each call (the `modelUsage` key in
the command-line client's JSON result), not the model's own description.

Each attempt is one call of the Claude Code command-line client in
non-interactive mode (`claude -p`), started in an empty temporary
directory, with all tools disabled (`--tools ""`, `--disallowedTools
"mcp__*"`, `--strict-mcp-config` with no servers), no session persistence,
and the system prompt `You are a careful software engineer.` The translator
receives everything in the prompt text and cannot read the repository or
any file. The main process extracts the code from the reply and writes it
to disk.

Conditions:

- **A**: one-shot, with `cobol_equiv.runtime`. Prompt A (section 7).
- **B**: each A attempt continued with up to 3 repair rounds. Before each
  round, the current version is run on DEV. If it passes DEV, the attempt
  stops. Otherwise the next round gets prompt B with the current version
  and the feedback for the first failing DEV vector (DEV order: fixed
  vectors, then generated). The version after the last round is final.
- **C**: one-shot, Python standard library only, no runtime. Prompt C.

Attempts: 3 independent attempts per program for A and C (separate calls
with identical prompts). B has 3 attempts per program, one starting from
each A attempt.

Per attempt the following is committed: the exact prompt, the raw reply
(the client's JSON result), the extracted translation, the UTC timestamp,
the model name and the client version.

Code extraction: the first fenced code block whose info string is
`python`; if there is none, the first fenced code block; if there is none,
the attempt has no code and fails as "crash or syntax error".

## 4. Running translations

Translations run in a separate Python 3.12 process per attempt, with a
time limit of the spec's `timeout` (10 s unless the spec sets another) per
vector and 600 s per attempt. Conditions A and B run with the repository's
virtual environment (`python -I`); condition C runs with `python3.12 -I -S`
so that only the standard library is importable. An import of anything
else fails the attempt.

Generating translations is not reproducible. Verifying them is: one command
re-runs the harness over all committed translations and compares the
result with the committed result files; CI runs it.

## 5. Measurements

Per track and condition:

- **Pass rate on HELD-OUT**: passing attempts / all attempts, with a
  Wilson 95% interval (z = 1.959964). Attempts of one program are not
  independent; the interval treats them as if they were, and this is
  stated next to it.
- **pass@3**: programs where at least one of the 3 attempts passes /
  programs, with a Wilson 95% interval.
- **Pass rate on VISIBLE alone**, same form, to show the gap between
  passing the shown examples and passing HELD-OUT.
- **Condition B by round**: HELD-OUT pass rate after rounds 0 (the A
  attempt), 1, 2 and 3; an attempt that stopped earlier keeps its last
  version.

Paired comparisons, per track: A vs C, pairing attempt i of A with attempt i
of C on the same program; A vs B, pairing each A attempt with the B attempt
started from it. Test: exact McNemar test (two-sided binomial test on the
discordant pairs, p = 0.5). Secondary: the same test on program-level
pass@3. The four primary p-values (2 comparisons x 2 tracks) are reported
raw and Holm-adjusted; significance level 0.05. Overlapping intervals are
not used as a test.

Secondary oracle: every translation that passes HELD-OUT on 3.1.2 is run on
the same HELD-OUT inputs with expected outputs from GnuCOBOL 3.2. Those that
pass on 3.1.2 and fail on 3.2 are listed.

## 6. Failure taxonomy

Every final attempt (A, B after its last round, C) that fails HELD-OUT gets
one category, from its first failing HELD-OUT vector (in the order:
generated, then boundary):

| category | assigned when |
|---|---|
| unsupported runtime feature | the runtime's Unsupported error was triggered (automatic) |
| crash or syntax error | no code, syntax error, import error, an exception, a timeout, or no `main` (automatic) |
| rounding | a wrong digit in the last decimal places from ROUNDED or from default truncation of decimals |
| truncation | high-order truncation, a value wider than its PICTURE, or ON SIZE ERROR handling |
| sign handling | a sign lost, added or encoded wrongly (overpunch, packed sign, negative zero, unsigned items) |
| PICTURE editing | a numeric-edited or alphanumeric-edited result formatted wrongly |
| string statements | STRING, UNSTRING, INSPECT or reference modification |
| file handling | reading or writing records: padding, trailing spaces, record length, end of file |
| loop or branch logic | control flow: wrong branch, wrong record processed, wrong count of iterations |
| other | none of the above |

The two automatic categories come from the harness result. For the others,
the first differing field is traced to the COBOL statement that produced
it and the category of that statement's semantics is chosen; the reason is
recorded in one line per attempt in `benchmark/failures.csv`. One example
difference per category is shown in the report, linked to
`docs/semantic-traps.md` where a trap there matches.

## 7. Prompts

`{...}` marks text filled in per program or attempt. The filled-in prompt of
every attempt is committed.

### IO contract (included in every prompt)

```text
The Python module must define

    def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]

- stdin: everything the program reads with ACCEPT (one ACCEPT reads one line).
- input_files: for every file the program reads, the name in its ASSIGN
  clause mapped to the full content of the file. LINE SEQUENTIAL files are
  lines that end with "\n".
- The return value is all bytes the program writes to standard output, and
  a dict that maps the ASSIGN name of every file the program writes to the
  full content of that file.
- The module must not read the clock, random sources, the network or the
  file system, and must not start processes. It runs on Python 3.12.
```

### Examples (included in every prompt)

For each VISIBLE vector `k`:

```text
### Example {k}
stdin = {Python bytes literal}
input_files = {Python dict of name -> bytes literal}
expected stdout = {Python bytes literal}
expected output_files = {Python dict of name -> bytes literal}
```

### Prompt A

````text
Translate the COBOL program below into a Python module.

The module must behave exactly like the program compiled with GnuCOBOL 3.1.2
(cobc -x -std=default): for every valid input it must produce byte for byte
the same standard output and output files.

Use the Python package cobol_equiv.runtime, documented in the API reference
below, for COBOL data and statements. You may also use the Python standard
library. No other packages are installed.

## IO contract
{IO contract}

## Examples
These are inputs and the exact outputs of the COBOL program.
{Examples}

## API reference: cobol_equiv.runtime
{API reference sheet}

## COBOL program
```cobol
{COBOL source}
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
````

### Prompt C

Prompt A with two changes: the paragraph starting "Use the Python package"
is replaced by

```text
Use only the Python standard library. No other packages are installed.
```

and the "API reference" section is left out.

### Prompt B (repair round)

Prompt A up to and including the COBOL program, followed by:

````text
## Your previous translation
```python
{current version}
```

## Test result
The previous translation was run on a test input that is not one of the
examples above.
{feedback}

Fix the translation. Reply with the complete corrected Python module in one
```python code block. Do not write anything after the code block.
````

`{feedback}` is, for an output difference:

```text
stdin = {Python bytes literal}
input_files = {Python dict of name -> bytes literal}
First difference: {Difference.describe() of the harness}
```

and for a crash, timeout or missing code: the same two input lines,
followed by `The translation raised {type}: {message}` (or `timed out`, or
`no Python code block was found in the reply`). Input literals longer than
4000 characters are cut at 4000 characters and marked `...(cut)`; the
message is cut at 500 characters.

### API reference sheet

Generated by a script from the signatures and docstrings of the public names
of `cobol_equiv.runtime` and `cobol_equiv.runtime.files`, then reviewed so
that it describes how to call the API and contains no statement taken from
`docs/findings.md`, `docs/semantic-traps.md` or any `mutants.py`. The exact
sheet used is committed, and its SHA-256 is recorded in
`benchmark/manifest.json`, before the first translation.

## 8. Order of work

1. This protocol (merged first).
2. Corpus of both tracks, specs, vector split, API sheet, runner.
3. Translation runs and their artifacts.
4. Analysis, taxonomy and report.

`benchmark/manifest.json` records the state after each completed unit of
work, so that the work can be resumed from it.

## Deviations from protocol

None so far.

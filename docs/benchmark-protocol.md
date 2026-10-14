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
   `1f037d24326124f4f2c5cd2d31e5220ceb549580`), licensed CC BY 4.0
   (`LICENSE` at that commit). Programs are committed with attribution and
   the license notice; every change is marked.
2. Rosetta Code COBOL solutions, through the RosettaCodeData mirror
   (`github.com/acmeism/RosettaCodeData`, commit
   `1d475861d7141ef2fafff293d9339f56e4b0f5db`). Rosetta Code content is under
   the GNU Free Documentation License; redistribution of code under it is
   not clearly allowed without that license's conditions, so these programs
   are not committed. A script downloads each one from
   `https://raw.githubusercontent.com/acmeism/RosettaCodeData/<commit>/Task/<task>/COBOL/<file>`
   and checks its SHA-256; adaptations are committed as patches.
3. NIST COBOL85 test suite, `newcob.val` inside
   `https://downloads.sourceforge.net/project/gnucobol/nist/newcob.val.tar.gz`
   (SHA-256 `e4513f26a9b38911f7bf882fe3d3339a80b45cabc2caf85eb3055b0f5ce87ee0`).
   No license text comes with the file, so it is treated as not clearly
   redistributable and downloaded by the same script.

A candidate is kept only if all of the following hold:

- **E1** It compiles with GnuCOBOL 3.1.2 (`cobc -x -std=default`, plus
  `-free` for a program written in free format) after the adaptations
  allowed below.
- **E2** It is deterministic: no clock, date, random numbers, environment
  variables or command-line arguments.
- **E3** Its output depends on input read with ACCEPT or from a sequential
  file, so that held-out inputs can be generated, and each input (stdin or
  file) can be described by one record layout (every line or record of it
  has the same fields). A program whose task
  statement (the Rosetta Code task, or the course text for the lab) names an
  input that the program hardcodes is adapted to read that input instead;
  without such a statement the candidate fails E3.
- **E4** It is inside the runtime subset documented in `docs/runtime.md`: a
  reference translation using `cobol_equiv.runtime` passes all its fixed,
  generated and boundary vectors on GnuCOBOL 3.1.2. If the reference hits
  `Unsupported`, `MoveError` or `PicError` of the runtime on any vector, the
  candidate fails E4; a reference that fails for any other reason is fixed
  until it passes. Reference translations are never shown to a translator.
- **E5** It has at most 500 lines, comments included.
- **E6** No CALL, COPY, embedded SQL or CICS, SORT/MERGE, indexed or
  relative files, SCREEN SECTION or REPORT SECTION.

Allowed adaptations, each listed per program in its `ADAPTATION.md`:
ASSIGN names and ORGANIZATION LINE SEQUENTIAL or SEQUENTIAL for files;
removing JCL or platform-only clauses (e.g. `RECORDING MODE`, `LABEL
RECORDS`, `BLOCK CONTAINS`); removing sequence numbers in columns 1-6 and
73-80; replacing a hardcoded task input with ACCEPT or a file READ (E3);
ending the program with STOP RUN. Nothing else in the logic or data
definitions is changed.

Selection: candidates are screened in the source order above; within a
source, in alphabetical order of file name (course) or task name (Rosetta
Code), and in file order (NIST). For a Rosetta task with several COBOL
solutions, the solutions are screened in file-name order and only the first
that meets E1-E6 is kept. Every candidate that meets E1-E6 is kept, up to
30. The target is 20 or more; if fewer qualify, the real number is reported
and nothing is added to reach a target. The screening record (each
candidate, kept or the first criterion it fails, and why) is committed as
`benchmark/corpus-e/screening.csv`.

### Track R: programs written for this repository

The 10 programs in `corpus/` plus exactly 10 new programs, at least one for
each area the corpus lacks: nested PERFORM and GO TO flow, SEARCH ALL,
INITIALIZE, reference modification, COMPUTE with several operators, and
multi-level group items. The new programs meet E1, E2, E4, E5 and E6 and
read input from a sequential file. In documentation this track is
described only as "programs written for this repository".

### Specs and freeze

Each program has a spec (`spec.py`): input record layouts, generators,
fixed vectors and output layouts. For both tracks:

- Generator overrides (narrowing a field's values below what its PICTURE
  allows) are used only for a domain that the task statement or the
  program's own validation states, or to make identifier fields readable
  (e.g. account numbers of a fixed form); each override is listed in the
  program's `ADAPTATION.md` (Track E) or spec docstring (Track R) with its
  reason. The 10 existing Track R specs get these reasons added before the
  freeze; their generators are not changed.
- Track E fixed vectors: the sample input that comes with the program or
  its task, if any, and otherwise none.
- All programs, specs, adaptations, reference translations, materialised
  vectors and expected outputs of both tracks are committed and frozen
  before the first translation call. No translator is called on a
  benchmark program before that point; the translation runner is tested
  only on a program outside both tracks.

### Source shown to the translator

For both tracks the source is shown with these removals only: comment lines
(indicator `*` or `/` in column 7 of fixed format), inline comments
starting with `*>` outside literals, and columns 73-80 of fixed format.

## 2. Vectors

The inputs are generated once, written to committed files, and then used as
fixed lists; nothing is generated or shrunk during scoring. Generation uses
Hypothesis 6.169.0 (pinned in `requirements-repro.txt`) with the generators
of the spec; a seed is `zlib.crc32` of the UTF-8 text given below. Every
generated input is kept in generation order; inputs identical to an
earlier one in any set are dropped and not replaced.

- **VISIBLE**: the first 2 generated inputs from the seed
  `"visible:" + name` that are not empty (every input file or stdin has at
  least one record). Shown to the translator with their outputs.
- **DEV**: all fixed vectors of the spec, then up to 50 generated inputs
  from the seed `"dev:" + name`. Used only for repair feedback in
  condition B.
- **HELD-OUT**: up to 200 generated inputs from the seed `name`, then all
  boundary vectors of `harness/boundary.py`. Never shown to any translator.
  The final score uses HELD-OUT only.

Expected outputs are the outputs of the program compiled with GnuCOBOL
3.1.2 (and, for the secondary oracle, 3.2), computed once and committed. An
input on which the COBOL program exits with a non-zero status or exceeds
its time limit is removed from its set and listed; this is done when the
vectors are materialised, before any translation. A program that loses more
than 10% of its HELD-OUT inputs this way is excluded.

Inputs follow the record layouts of the program: numeric fields hold
digits (with the sign encoding of their USAGE), alphanumeric fields hold
printable ASCII. For stdin and LINE SEQUENTIAL files, one record is one
line with trailing spaces removed; for SEQUENTIAL files, records are
concatenated at full length (the generator is extended for this before the
freeze). Boundary vectors do not
use the generator overrides, so they include values the program may treat
as invalid (it must still behave like the COBOL program on them).

A translation **passes** a set of vectors when, for every vector in it, its
standard output and every output file are byte-identical to the expected
ones, it does not raise, does not exceed the time limit, and does not
trigger the runtime's `Unsupported` error (also when it catches it).

## 3. Translators and conditions

Model: one model ID, written in `benchmark/manifest.json` before the first
call and passed to every call with `--model`; no fallback model. For each
call the model IDs reported in the client's JSON result (`modelUsage`) are
recorded. A call that reports any other model ID is invalid, logged, and
repeated, at most 5 times; if a call is still invalid after that, the run
stops and the cause is recorded as a deviation. The runner test on the
outside program checks the model IDs reported and that the client works
with an empty home directory.

Each call is one run of the Claude Code command-line client in
non-interactive mode (`claude -p`), started in an empty temporary directory
with an empty home directory, with: `--safe-mode`, `--setting-sources ""`,
`--tools ""`, `--disallowedTools "mcp__*"`, `--strict-mcp-config` with no
servers, `--disable-slash-commands`, `--no-session-persistence`, and the system
prompt
`You are a careful software engineer.` Sampling settings are the client's
defaults (they cannot be set); the client version is recorded. The
translator receives everything in the prompt text and cannot read the
repository or any file. The runner extracts the code from the reply and
writes it to disk.

Conditions:

- **A**: one-shot, with `cobol_equiv.runtime`. Prompt A (section 7).
- **B**: each A attempt continued with up to 3 repair rounds. Before each
  round, the current version is run on DEV. If it passes DEV, the attempt
  stops. Otherwise the next round is a new call with prompt B, which holds
  the current version and the feedback for its first failing DEV vector
  (in DEV order); earlier versions and feedback are not included. The
  version after the last round is final.
- **C**: one-shot, Python standard library only, no runtime. Prompt C.

Attempts: 3 independent attempts per program for A and C (separate calls
with identical prompts), numbered 1-3 in the order they were made. B
attempt i starts from A attempt i.

Every call is logged. For every call the following is committed: the exact
prompt, the raw reply (the client's JSON result), the extracted code, the
UTC timestamp, the model IDs and the client version.

Errors: a call that returns no result (transport error, rate limit, client
failure, `is_error` set) is retried, at most 5 times; after that the call
counts as having no code. A reply without a code block, an empty reply or a
refusal counts as having no code.

Code extraction: the first fenced code block whose info string is
`python`; if there is none, the first fenced code block; if there is none,
the call has no code, and the attempt fails as "crash or syntax error".

## 4. Running translations

Every translation runs in a child process that receives only the inputs
(never the expected outputs), runs `main` on each vector with the spec's
`timeout` (10 s unless the spec sets another) per vector, 600 s in total
and 2 GiB of address space, and returns the outputs and any exception. The
parent process compares them with the expected outputs.

- A and B: Python 3.12 of the repository's virtual environment, `-I`. The
  child also reports whether the runtime's `Unsupported` error was raised.
  The translation runs in the same process as that check, so a translation
  could reset the counter; this is not guarded against.
- C: `python3.12 -I -S`, so only the standard library can be imported; an
  import of anything else is an exception like any other.

The runtime and harness are frozen at the commit recorded in
`benchmark/manifest.json` before the first call (with the versions of
Python, Hypothesis, GnuCOBOL and the client). A later change to either that
affects results is a deviation.

Generating translations is not reproducible. Verifying them is: one command
re-runs every committed translation on the committed vectors and compares
the result with the committed result files; CI runs it.

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

Paired comparisons, per track:

- **Primary**: exact McNemar test (two-sided binomial test with p = 0.5 on
  the discordant pairs; p = 1 when there are none) for A vs C, pairing A
  attempt i with C attempt i of the same program, and for A vs B, pairing A
  attempt i with B attempt i. The four primary p-values (2 comparisons x 2
  tracks) are reported raw and Holm-adjusted; significance level 0.05. The
  three pairs of a program are not independent, which the test assumes;
  this is stated with the result.
- **Sensitivity** (accounts for that dependence): exact two-sided sign test
  over programs on the per-program difference in passing attempts (0-3),
  ties dropped.
- **Exploratory**: McNemar on program-level pass@3. Not adjusted.

Overlapping intervals are not used as a test.

Secondary oracle: every final translation that passes HELD-OUT on 3.1.2 is
run on the same HELD-OUT inputs against the GnuCOBOL 3.2 outputs. Those
that pass on 3.1.2 and fail on 3.2 are listed.

## 6. Failure taxonomy

Every final attempt (A, B after its last round, C) that fails HELD-OUT gets
exactly one category, from its first failing HELD-OUT vector (list order):

| category | assigned when |
|---|---|
| unsupported runtime feature | the runtime raised `Unsupported`, `MoveError` or `PicError` (automatic) |
| crash or syntax error | no code, syntax error, import error, any other exception, a time-out (per vector or total), or no `main` (automatic) |
| rounding | a wrong digit in the low-order decimal places, from ROUNDED or from dropping extra decimal places |
| truncation | wrong high-order digits: a value wider than its PICTURE, or ON SIZE ERROR handling |
| sign handling | a sign lost, added or encoded wrongly (overpunch, packed sign, negative zero, unsigned items) |
| PICTURE editing | a numeric-edited or alphanumeric-edited result formatted wrongly |
| string statements | STRING, UNSTRING, INSPECT or reference modification |
| file handling | reading or writing records: padding, trailing spaces, record length, end of file |
| loop or branch logic | control flow: wrong branch, wrong record processed, wrong number of iterations |
| other | none of the above |

The two automatic categories come from the child process result. For the
rest, the first differing field is traced to the COBOL statement that first
produced a wrong value, and the category of that statement's semantics is
chosen. If two categories fit, the first in this order wins: sign handling,
rounding, truncation, PICTURE editing, string statements, file handling,
loop or branch logic, other. Classification is done on a list in random
order (seed `crc32("taxonomy")`) that shows program, COBOL source,
translation code and difference but not the condition; the reason is
recorded in one line per attempt in `benchmark/failures.csv`. One example
difference per category is shown in the report, linked to
`docs/semantic-traps.md` where a trap there matches.

## 7. Prompts

`{...}` marks text filled in per program or call. The filled-in prompt of
every call is committed.

### IO contract (included in every prompt)

```text
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
(cobc -x -std=default): for every input whose records fit the program's
record descriptions, it must produce byte for byte the same standard output
and output files.

Use the Python package cobol_equiv.runtime, documented in the API reference
below, for COBOL data and statements. Besides it, use only the Python
standard library.

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
Use only the Python standard library. The module runs in an interpreter
that has no other packages.
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

and otherwise the same two input lines followed by one of: `The
translation raised {type}: {message}`, `The translation timed out.`, `No
Python code block was found in the reply.` Input literals longer than 4000
characters are cut at 4000 characters and marked `...(cut)`; the message is
cut at 500 characters. `Difference.describe()` names fields after the
spec's output layout; those names are part of the feedback.

### API reference sheet

Generated by a script from the signatures and docstrings of the public names
of `cobol_equiv.runtime` and `cobol_equiv.runtime.files`, then reviewed so
that it describes how to call the API and contains no statement taken from
`docs/findings.md`, `docs/semantic-traps.md` or any `mutants.py`. The exact
sheet used is committed, and its SHA-256 is recorded in
`benchmark/manifest.json`, before the first call.

## 8. Threats to validity (reported with the results)

- One model, one date, client default sampling settings.
- Track E programs are public; they, or their task statements, may be in
  the model's training data.
- Track R programs were written for this repository together with the
  harness, and exercise what the harness checks.
- GnuCOBOL is the oracle; no IBM compiler was used.
- The corpus is small, and the Wilson intervals and the primary McNemar
  test treat the attempts of one program as independent.
- Failure categories are assigned by hand (blind to condition).

## 9. Order of work

1. This protocol (merged first).
2. Corpus of both tracks, specs, materialised vectors, API sheet, runner.
3. Translation runs and their artifacts.
4. Analysis, taxonomy, report and documentation.

`benchmark/manifest.json` records the state after each completed unit of
work, so that the work can be resumed from it.

## Deviations from protocol

All deviations below were decided during corpus construction (step 2),
before any translation call.

- **D1 (allowed adaptations).** Adding the missing period after the
  PROGRAM-ID paragraph is treated as an allowed adaptation. GnuCOBOL 3.1.2
  rejects `PROGRAM-ID. CBL0001` without it (3.2 accepts it); the course
  program CBL0001 needs it (`benchmark/corpus-e/omp-cbl0001/ADAPTATION.md`).
- **D2 (E4 and scoring).** Besides `Unsupported`, `MoveError` and
  `PicError`, two other runtime refusals count as "outside the runtime
  subset" for E4: `DataError` (invalid data in a numeric item) and an
  out-of-range subscript (`IndexError` from the runtime's storage). In both
  cases GnuCOBOL without runtime checks continues with undefined data,
  which the runtime does not model. Two Rosetta candidates fail E4 for
  these reasons (`screening.csv`). In scoring, a translation that raises
  `DataError` is reported with the runtime refusals (kind "unsupported");
  any `IndexError` is reported as an error, because a translation's own
  indexing cannot be told apart from the runtime's. Both are failures.
- **D3 (where Track E adaptations are recorded).** For the Rosetta Code
  programs, which are downloaded and not committed, the adaptations are the
  exact edits in `adaptation.json` and the overrides, fixed vectors and
  adaptations are described in the docstring of `spec.py`; there is no
  `ADAPTATION.md`. The course programs have an `ADAPTATION.md`.
- **D4 (Track R overrides).** Three of the new Track R programs (namefmt,
  luhn, wordwrap) override an alphanumeric input with the format their
  header comment states ("LAST,FIRST MIDDLE", card numbers, words), mixed
  with unrestricted text; this is a domain stated by the program, but in a
  comment rather than in its validation. Several overrides of the 10
  existing Track R specs narrow a field without a stated domain (for
  example balances, rates and hours to realistic ranges). The protocol
  requires both that overrides have a stated domain and that the existing
  generators are not changed; the generators were kept and each such
  override is labelled "not stated by the program" in its spec docstring.
- **D5 (vector loss as an exclusion reason).** Three Rosetta candidates
  that meet E1-E6 are excluded because more than 10% of their HELD-OUT
  inputs would be removed (section 2): the program does not end, exceeds
  the time limit, or exits with an error on most inputs. They are listed
  in `screening.csv` with criterion "vectors".

- **D6 (generation).** Hypothesis 6.169.0 mixes literal constants from
  the project's imported modules into generated values, so the inputs
  depended on which modules were loaded. Vector generation (and the
  harness's own checks) now turn this off (`no_local_constants` in
  `harness/strategies.py`), so that a set depends only on the spec and the
  seed text of section 2. The vectors were materialised with this setting.
- **D7 (API sheet).** The sheet is generated from the signatures of the
  public names, but each docstring is replaced by a description written
  during the review (in `benchmark/apisheet.py`), because several
  docstrings state GnuCOBOL behaviours. Internal helpers (`edit`,
  `store_numeric`, `store_cobdec`, `Pic`, `parse_pic`) are left out.

- **D8 (repair rounds).** A repair reply without a code block leaves the
  current version unchanged; the next round shows that version again (the
  round still counts). Feedback for a translation that raised `Unsupported`
  and caught it reads "The translation hit an unsupported runtime feature
  N time(s) (Unsupported was raised and caught)."
- **D9 (client environment).** The client gets only an allowlist of
  environment variables (path, locale, proxy and certificates, API
  endpoint, credentials; `ENV_ALLOWLIST` in `benchmark/translate.py`) besides the empty
  home directory, so that no setting of the session that starts the runs
  (for example an effort level) reaches the translator. Each call records
  the names of the variables passed. A call that fails authentication
  stops the run instead of counting as a call without code.
- **D10 (secondary oracle).** rc-csv-data-manipulation ends with file
  status 71 on every input under GnuCOBOL 3.2 (see its spec), so it has no
  3.2 expected outputs and is left out of the 3.2 re-run.

- **D11 (account limit).** During condition C, 18 calls failed because
  the account's usage limit was reached ("session limit"); the retries
  failed the same way. They are listed in
  `benchmark/results/account-limit-reruns.csv` (taken from the call records
  before they were deleted; those records were never committed). These are failures of the account, not of the
  translator: their artifacts were deleted and the calls were made again
  after the limit reset, under the same attempt numbers. The runner now stops on such a message instead
  of recording a call without code.

- **D12 (time limits).** (a)-(c) were decided after the translation runs,
  before any verification result was computed; (d) was added later, while
  the verification was running (units of it had been computed, but no
  aggregated result had been looked at), because the extended re-runs of
  translations that loop took hours. (a) A translation that is correct but slower than
  the limits of section 4 is not counted as failing: every vector that
  exceeds the per-vector limit (spec timeout, 10 s) or is not reached
  within the 600 s total is run again with 120 s per vector and 7200 s in
  total (`EXTENDED_TIMEOUT`, `EXTENDED_TOTAL` in `benchmark/runner.py`);
  if its output is then correct, the vector passes and is counted as
  "slow". (b) A vector that still times out is a time-out, a separate
  outcome: a translation whose only failing vectors are time-outs gets the
  verdict "timeout", which is reported in its own column and as its own
  failure category, not as "crash or syntax error" and not as a semantic
  failure. It does not count as a pass. (c) When the total limit stops a
  run, the results of the vectors finished before it are kept (before,
  all vectors of the run were marked as timed out). (d) The extended run
  of a translation stops after 3 vectors time out again
  (`EXTENDED_MAX_TIMEOUTS`); its remaining late vectors stay time-outs
  without being run again. Such a translation cannot pass, so this only
  saves time; a late vector that would have given a wrong output is then
  counted as a time-out, not as a difference. (e) Consequently the failure
  of an attempt (for its verdict and its taxonomy category) is the first
  failing HELD-OUT vector in list order that is not a time-out, and
  "timeout" only when all failing vectors are time-outs; this replaces
  "first failing vector" of section 6 for attempts with time-outs. A vector
  that timed out after raising the runtime's `Unsupported` is counted as
  "unsupported". (f) The per-vector limit also covers loading the module,
  and a translation that catches the time-out exception is stopped 2 s
  later, the vector counted as a time-out. Condition B's DEV
  checks during generation used the original limits; that is unchanged.

- **D13 (API sheet error, found in the analysis).** The frozen API sheet
  describes `dec` as giving "CobDecimal ... for compute expressions and
  comparisons", but `CobDecimal` defines no comparison operators: `<` and
  `>` between two `CobDecimal` values raise `TypeError`, and `==` compares
  object identity, so `dec(x) == dec(y)` is always false. Most crashes of
  condition A raise the `TypeError`, and the time-outs of condition A are
  loops whose end test is such an equality (reasons in
  benchmark/results/failures.csv, counts in docs/benchmark.md). The sheet
  and the runtime were not changed after the runs, so condition A (and B,
  which starts from A) was measured with this error in its material;
  condition C does not use the sheet. The A vs C comparison is affected by
  it, and the report says so.

- **D14 (runtime defect corrected, sensitivity analysis, after the
  analysis).** The cause of D13 is a defect of the runtime, not only of
  the sheet: COBOL compares numeric values algebraically, and `CobDecimal`
  did not. Runtime 1.1.0 adds value-based `==`, `!=`, `<`, `<=`, `>`, `>=`
  and a hash consistent with them, checked against GnuCOBOL
  (`tests/oracle/test_compare.py`, docs/runtime.md). The runtime frozen for
  the benchmark (commit 50456a3) is called 1.0.0; that number was assigned
  afterwards. The registered results are unchanged and stay the primary
  results. The committed translations, unchanged, were verified again with
  the corrected runtime as a sensitivity analysis; the driver reproduces
  runtime 1.0.0 ("registered" mode: identity `==`, no ordering, identity
  hash) and 1.1.0 ("corrected" mode) in the same process setup, and counts
  the CobDecimal comparison calls each vector makes. Scope of the
  corrected-mode verification: the A and B translations in which the static
  scan (`python -m cobol_equiv.benchmark.eqscan`, results in
  benchmark/results/eq-sites.csv) finds a CobDecimal compared with `==`,
  `!=`, `<`, `<=`, `>`, `>=` or `in`, or hashed; every B attempt derived
  from such an A translation; and a fixed sample of 30 other A and B units
  (seed `crc32("d14-sample")`), whose verdicts must not change. The scan is
  approximate (values passed through containers, attributes or parameters
  are not followed); the sample is the check on what it misses. Condition
  C translations do not import the runtime (none mentions the package, and
  they run with `python -I -S`), so their verdicts cannot change and they
  were not run again. Outside the scope, the corrected verdicts are the
  registered ones. The registered mode was run on the same units and must
  reproduce verdicts.csv (it was reproduced in full on
  abdulazizbalu/cobol-equiv#8). The failures that change were categorised
  with the rules of section 6; a failure identical to a registered one
  keeps its category. Results are in docs/benchmark.md ("Sensitivity to
  the CobDecimal comparison defect"), generated from
  benchmark/results/verdicts-corrected.csv and failures-corrected.csv.

Notes, not deviations: the runtime was extended before the freeze, while
writing reference translations (ACCEPT from standard input, alphanumeric
to numeric conversion for items, truncation of arithmetic results stored
into edited items, reference modification). Each extension is checked
against GnuCOBOL 3.1.2 and 3.2 (`docs/runtime.md`). Track E selection used
the corpus as it was then; a candidate excluded for E4 is not re-screened
after a later runtime change. The child process that runs a translation is
not sandboxed from the file system: a translation could read the committed
vectors or write its own result file; the committed translations are
checked for file access when they are analysed. A condition C translation
that defines an exception class named like a runtime refusal (for example
`DataError`) is classed as "unsupported" rather than as a crash.

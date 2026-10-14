# Track E: external programs

Selection rules, sources and pins: `docs/benchmark-protocol.md`, section 1.
Every screened candidate, with the result and the criterion that excluded
it, is listed in `screening.csv` (columns: source, candidate, lines,
format, result, criterion, reason). Candidates after the cap of kept
programs was reached are listed as "not screened".

## Layout of a program directory

- `spec.py`: the program spec used by the harness. Its docstring records
  the input layout, every generator override with its reason, every
  adaptation and every fixed vector.
- `reference.py`: a reference translation using the runtime. It is used
  only to check criterion E4 and is never shown to a translator.
- `omp-*`: `original.cob` (the course file, unchanged), `program.cob` (the
  compiled program) and `ADAPTATION.md` (source path, license, changes).
  License: CC BY 4.0, `LICENSE-OMP-CC-BY-4.0.txt`.
- `rc-*`: `source.json` (pinned URL and SHA-256 of the solution, and of the
  task statement when the task gives sample input), optionally
  `adaptation.json` (exact find/replace edits, each must match once).
  Rosetta Code content is under the GNU Free Documentation License, so the
  COBOL files are not committed: `python -m cobol_equiv.benchmark.fetch`
  downloads them, checks the checksums and writes `original.cob`,
  `program.cob` and `task.txt` (all ignored by git). The reference
  translations of these programs are derived from the downloaded sources.

## Fixed vectors

Sample inputs given in a task statement or in the course data are used as
fixed vectors in the DEV set only (protocol, section 2); they are never
part of HELD-OUT.

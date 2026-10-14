Translate the COBOL program below into a Python module.

The module must behave exactly like the program compiled with GnuCOBOL 3.1.2
(cobc -x -std=default): for every input whose records fit the program's
record descriptions, it must produce byte for byte the same standard output
and output files.

Use only the Python standard library. The module runs in an interpreter
that has no other packages.

## IO contract
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

## Examples
These are inputs and the exact outputs of the COBOL program.
### Example 1
stdin = b'\n'
input_files = {}
expected stdout = b'Mary had a        lamb.\n'
expected output_files = {}

### Example 2
stdin = b'NIL\n'
input_files = {}
expected stdout = b'Mary had a NIL    lamb.\n'
expected output_files = {}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. interpolation-included.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  extra PIC X(6).

       PROCEDURE DIVISION.
           ACCEPT extra
           DISPLAY FUNCTION SUBSTITUTE("Mary had a X lamb.", "X", extra)

           GOBACK
           .
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.

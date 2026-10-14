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
stdin = b''
input_files = {'input.txt': b'\n'}
expected stdout = b'000001: \n000002: \n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'input.txt': b'\nXeIs7\nj@\nfkE|Uh3}ILC\n'}
expected stdout = b'000001: \n000002: XeIs7\n000003: j@\n000004: fkE|Uh3}ILC\n000005: fkE|Uh3}ILC\n'
expected output_files = {}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. read-file-line-by-line.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT input-file ASSIGN TO "input.txt"
               ORGANIZATION LINE SEQUENTIAL
               FILE STATUS input-file-status.

       DATA DIVISION.
       FILE SECTION.
       FD  input-file.
       01  input-record PIC X(256).

       WORKING-STORAGE SECTION.
       01  input-file-status PIC 99.
           88  file-is-ok    VALUE 0.
           88  end-of-file   VALUE 10.

       01  line-count        PIC 9(6).

       PROCEDURE DIVISION.
           OPEN INPUT input-file
           IF NOT file-is-ok
               DISPLAY "The file could not be opened."
               GOBACK
           END-IF

           PERFORM VARYING line-count FROM 1 BY 1 UNTIL end-of-file
               READ input-file
               DISPLAY line-count ": " FUNCTION TRIM(input-record)
           END-PERFORM

           CLOSE input-file

           GOBACK
           .
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.

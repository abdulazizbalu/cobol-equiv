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
input_files = {'VALUES.DAT': b'A00000\n'}
expected stdout = b'COUNT 001 TOTAL      0.00\n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'VALUES.DAT': b'B00000\n'}
expected stdout = b'COUNT 000 TOTAL      0.00\n'
expected output_files = {}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. TALLY.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT IN-FILE ASSIGN TO "VALUES.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD IN-FILE.
       01 IN-REC.
          05 IN-CODE        PIC X.
          05 IN-AMT         PIC 9(3)V99.
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-COUNT          PIC 9(3) VALUE 0.
       01 WS-TOTAL          PIC 9(5)V99 VALUE 0.
       01 WS-OUT            PIC ZZ,ZZ9.99.
       PROCEDURE DIVISION.
           OPEN INPUT IN-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ IN-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END
                       IF IN-CODE = "A"
                           ADD 1 TO WS-COUNT
                           ADD IN-AMT TO WS-TOTAL
                       END-IF
               END-READ
           END-PERFORM
           CLOSE IN-FILE
           MOVE WS-TOTAL TO WS-OUT
           DISPLAY "COUNT " WS-COUNT " TOTAL " WS-OUT
           STOP RUN.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
